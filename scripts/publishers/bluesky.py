#!/usr/bin/env python3
"""Publish a single post to Bluesky. Standalone CLI.

Usage:
  # Root post
  bluesky.py --text "Hello, Bluesky."

  # Reply to an existing post
  bluesky.py --text "Replying." \\
      --reply-to-uri at://did:plc:.../app.bsky.feed.post/abc \\
      --reply-to-cid bafyrei...

  # Reply deep in a thread (parent != root)
  bluesky.py --text "Replying in thread." \\
      --reply-to-uri <parent_uri> --reply-to-cid <parent_cid> \\
      --root-uri <root_uri>     --root-cid <root_cid>

  # Quote post (embed another post as a record)
  bluesky.py --text "Commentary on this post." \\
      --quote-uri at://did:plc:.../app.bsky.feed.post/abc \\
      --quote-cid bafyrei...

  # Reply and quote together (yes, you can do both)
  bluesky.py --text "Replying while quoting something else." \\
      --reply-to-uri <parent_uri> --reply-to-cid <parent_cid> \\
      --quote-uri    <quoted_uri> --quote-cid    <quoted_cid>

If --root-uri/--root-cid are omitted, they default to --reply-to-uri /
--reply-to-cid (i.e. a direct reply to a root post).

Reads credentials from the environment:
  BLUESKY_HANDLE          e.g. andysmith.ai (domain handles work)
  BLUESKY_APP_PASSWORD    create at https://bsky.app/settings/app-passwords

On success, prints one JSON line to stdout and exits 0:
  {"id": "at://did:plc:.../app.bsky.feed.post/...", "cid": "bafyrei..."}

On failure, prints an error to stderr and exits non-zero.

This script is intentionally dumb: it does not know about cards, character
budgets, or frontmatter. It posts a string and reports the result. The card
layer (thinkbox/scripts/publish.py) drives it as one of many platforms.
"""

import argparse
import json
import os
import re
import sys

from atproto import Client, models

URL_RE = re.compile(r"https?://\S+")


def require_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        sys.stderr.write(f"error: missing environment variable {name}\n")
        sys.exit(2)
    return value


def build_reply_ref(args: argparse.Namespace):
    """Return a ReplyRef if reply args were supplied, else None."""
    has_parent_uri = bool(args.reply_to_uri)
    has_parent_cid = bool(args.reply_to_cid)
    if not (has_parent_uri or has_parent_cid):
        return None
    if not (has_parent_uri and has_parent_cid):
        sys.stderr.write(
            "error: --reply-to-uri and --reply-to-cid must be given together\n"
        )
        sys.exit(2)

    root_uri = args.root_uri or args.reply_to_uri
    root_cid = args.root_cid or args.reply_to_cid

    parent = models.ComAtprotoRepoStrongRef.Main(
        uri=args.reply_to_uri, cid=args.reply_to_cid
    )
    root = models.ComAtprotoRepoStrongRef.Main(uri=root_uri, cid=root_cid)
    return models.AppBskyFeedPost.ReplyRef(parent=parent, root=root)


def build_embed(args: argparse.Namespace):
    """Return an embed object if quote args were supplied, else None.

    For now this only builds record embeds (quote posts). Image, external,
    and video embeds can be added alongside if/when the card layer needs
    them.
    """
    has_uri = bool(args.quote_uri)
    has_cid = bool(args.quote_cid)
    if not (has_uri or has_cid):
        return None
    if not (has_uri and has_cid):
        sys.stderr.write(
            "error: --quote-uri and --quote-cid must be given together\n"
        )
        sys.exit(2)

    quoted = models.ComAtprotoRepoStrongRef.Main(
        uri=args.quote_uri, cid=args.quote_cid
    )
    return models.AppBskyEmbedRecord.Main(record=quoted)


def build_images_embed(image_paths: list[str], client) -> object | None:
    """Upload images and return an images embed, or None.

    Each path must be a local file. Uploaded via com.atproto.repo.uploadBlob.
    Bluesky allows up to 4 images per post.
    """
    if not image_paths:
        return None
    if len(image_paths) > 4:
        sys.stderr.write("error: maximum 4 images per post\n")
        sys.exit(2)
    images = []
    for path in image_paths:
        try:
            with open(path, "rb") as f:
                img_bytes = f.read()
        except OSError as e:
            sys.stderr.write(f"error: cannot read --image {path}: {e}\n")
            sys.exit(2)
        upload = client.upload_blob(img_bytes)
        images.append(
            models.AppBskyEmbedImages.Image(
                image=upload.blob,
                alt="",
            )
        )
    return models.AppBskyEmbedImages.Main(images=images)


def build_external_embed(args: argparse.Namespace, thumb=None):
    """Return an external embed (link preview card) or None.

    Bluesky renders a link-preview card when a post carries an external
    embed with title/description and an optional thumbnail blob. Without
    it, URLs in facets are clickable but render inline, not as a rich
    card.

    `thumb` is a BlobRef previously uploaded via client.upload_blob(),
    or None. The blob upload itself happens in main() after login — this
    function just assembles the embed.
    """
    if not args.embed_uri:
        return None
    if not args.embed_title:
        sys.stderr.write("error: --embed-uri requires --embed-title\n")
        sys.exit(2)
    external = models.AppBskyEmbedExternal.External(
        uri=args.embed_uri,
        title=args.embed_title,
        description=args.embed_description or "",
        thumb=thumb,
    )
    return models.AppBskyEmbedExternal.Main(external=external)


def build_facets(text: str):
    """Build link facets for every URL in text. None if no URLs.

    Bluesky does NOT auto-detect URLs in plain text — without a facet
    entry mapping a byte range to a link feature, the URL is inert.
    Offsets are BYTE offsets in the UTF-8 encoding, not character
    offsets, so multi-byte characters (em dashes etc.) are handled
    correctly.
    """
    facets = []
    for m in URL_RE.finditer(text):
        url = m.group(0)
        # Trailing punctuation shouldn't be part of the link.
        stripped = url.rstrip(".,;:!?)")
        if not stripped:
            continue
        byte_start = len(text[: m.start()].encode("utf-8"))
        byte_end = byte_start + len(stripped.encode("utf-8"))
        facets.append(
            models.AppBskyRichtextFacet.Main(
                features=[models.AppBskyRichtextFacet.Link(uri=stripped)],
                index=models.AppBskyRichtextFacet.ByteSlice(
                    byte_start=byte_start, byte_end=byte_end,
                ),
            )
        )
    return facets or None


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Publish a single post to Bluesky."
    )
    parser.add_argument("--text", required=True, help="Post text")
    parser.add_argument(
        "--reply-to-uri",
        help="AT URI of parent post to reply to (at://did:plc:.../...)",
    )
    parser.add_argument(
        "--reply-to-cid", help="CID of parent post (bafyrei...)"
    )
    parser.add_argument(
        "--root-uri",
        help="AT URI of thread root (default: same as --reply-to-uri)",
    )
    parser.add_argument(
        "--root-cid",
        help="CID of thread root (default: same as --reply-to-cid)",
    )
    parser.add_argument(
        "--quote-uri",
        help="AT URI of a post to quote (embed as a record)",
    )
    parser.add_argument(
        "--quote-cid", help="CID of the quoted post (bafyrei...)"
    )
    parser.add_argument(
        "--embed-uri",
        help="URL for an external link preview card (source article, etc.)",
    )
    parser.add_argument(
        "--embed-title",
        help="Title for the external link preview (required with --embed-uri)",
    )
    parser.add_argument(
        "--embed-description",
        help="Description for the external link preview (optional)",
    )
    parser.add_argument(
        "--embed-thumb",
        help=(
            "Local path to a thumbnail image for the external link preview. "
            "Uploaded as a blob via com.atproto.repo.uploadBlob and attached "
            "as `thumb` on the embed. Optional."
        ),
    )
    parser.add_argument(
        "--image",
        action="append",
        default=[],
        help=(
            "Local path to an image to attach. Can be repeated up to 4 times. "
            "Cannot be combined with --embed-uri or --quote-uri."
        ),
    )
    args = parser.parse_args()

    handle = require_env("BLUESKY_HANDLE")
    app_password = require_env("BLUESKY_APP_PASSWORD")

    reply_to = build_reply_ref(args)
    quote_embed = build_embed(args)

    client = Client()
    client.login(handle, app_password)

    # Upload the thumbnail blob (if any) before assembling the embed.
    # Blob upload requires an authenticated client, so it must happen
    # after login. The returned blob ref goes into AppBskyEmbedExternal.
    thumb = None
    if args.embed_thumb:
        if not args.embed_uri:
            sys.stderr.write(
                "error: --embed-thumb requires --embed-uri\n"
            )
            sys.exit(2)
        try:
            with open(args.embed_thumb, "rb") as f:
                thumb_bytes = f.read()
        except OSError as e:
            sys.stderr.write(
                f"error: cannot read --embed-thumb {args.embed_thumb}: {e}\n"
            )
            sys.exit(2)
        upload_response = client.upload_blob(thumb_bytes)
        thumb = upload_response.blob

    external_embed = build_external_embed(args, thumb=thumb)
    images_embed = build_images_embed(args.image, client)

    embeds = [e for e in [quote_embed, external_embed, images_embed] if e]
    if len(embeds) > 1:
        names = []
        if quote_embed:
            names.append("--quote-uri")
        if external_embed:
            names.append("--embed-uri")
        if images_embed:
            names.append("--image")
        sys.stderr.write(
            f"error: cannot combine {' and '.join(names)} "
            "(only one embed type per post)\n"
        )
        sys.exit(2)
    embed = embeds[0] if embeds else None

    facets = build_facets(args.text)

    response = client.send_post(
        text=args.text, facets=facets, reply_to=reply_to, embed=embed
    )

    print(json.dumps({"id": response.uri, "cid": response.cid}))


if __name__ == "__main__":
    main()
