#!/usr/bin/env python3
"""Publish a card: fan out to all configured platforms.

Reads content/cards/<uuid>.md, resolves its card_reply_to / card_ref
chain against other cards' card_published[] entries for each target
platform, posts the body via that platform's wrapper script
(thinkbox/scripts/publishers/<p>.sh), parses the JSON result, and
appends one card_published[] entry per successful publish.

Thread-root walking: for a reply card C whose chain is C → B → A,
the AT Protocol (and similar platforms) need BOTH the parent reference
(B) AND the thread root reference (A). This module walks card_reply_to
all the way up to the topmost card to find the root — so deep threads
work, not only direct replies to a root.

Refuses cleanly if:
  - The card already has a card_published[] entry for a target platform
    (per-platform double-post refusal)
  - A linked card (parent, thread root, ref target) is not yet on the
    target platform — publish the dependency first
  - A linked card file is missing
  - The body exceeds the 300-char limit (URLs never belong in card
    bodies; external refs flow through card_bib as a link preview embed)
"""

import argparse
import io
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from ruamel.yaml import YAML

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent.parent  # thinkbox/scripts -> thinkbox -> repo root
CONTENT_DIR = ROOT / "content"
CARDS_DIR = CONTENT_DIR / "cards"
BIB_DIR = CONTENT_DIR / "bib"
PUBLISHERS_DIR = SCRIPT_DIR / "publishers"

# Hardcoded fan-out targets. Adding a new platform = drop a new
# publishers/<name>.{sh,py} pair and append the name here.
PLATFORMS = ["bluesky"]

# Cards must not contain URLs in the body; external references flow
# through card_bib and become a link-preview embed on publish. So the
# char count is just the visible body length.
LIMIT = 300

# Round-trip YAML for the target card's frontmatter (preserves comments,
# key order, existing quoting).
yaml_rt = YAML(typ="rt")
yaml_rt.preserve_quotes = True
yaml_rt.indent(mapping=2, sequence=4, offset=2)
yaml_rt.width = 4096  # avoid line wrapping

# Safe YAML for the read-only snapshot of sibling cards we use during
# reply/ref resolution.
yaml_safe = YAML(typ="safe")


def count_chars(text: str) -> int:
    return len(text)


def split_frontmatter(text: str) -> tuple[str, str]:
    if not text.startswith("---\n"):
        raise SystemExit("error: card file has no YAML frontmatter")
    end = text.find("\n---\n", 4)
    if end == -1:
        raise SystemExit("error: card file frontmatter is not terminated")
    return text[4 : end + 1], text[end + len("\n---\n") :]


def assemble(fm_text: str, body: str) -> str:
    return "---\n" + fm_text + "---\n" + body


def load_bib(bib_uuid: str) -> tuple[dict | None, str]:
    """Return (frontmatter_dict, body_stripped) for a bib entry, or (None, "").

    Used for building external link-preview embeds on platforms that
    support them (Bluesky): title from bib_title, description from the
    first paragraph of the bib body, uri from bib_url.
    """
    bib_path = BIB_DIR / f"{bib_uuid}.md"
    if not bib_path.exists():
        return None, ""
    try:
        raw = bib_path.read_text()
    except OSError:
        return None, ""
    if not raw.startswith("---\n"):
        return None, ""
    end = raw.find("\n---\n", 4)
    if end == -1:
        return None, ""
    try:
        fm = yaml_safe.load(io.StringIO(raw[4 : end + 1])) or None
    except Exception:
        return None, ""
    body = raw[end + len("\n---\n") :].strip()
    if not isinstance(fm, dict):
        return None, body
    return fm, body


def load_all_cards() -> dict:
    """Return {uuid: frontmatter_dict} for every card in content/cards/.

    Read-only snapshot used for card_reply_to / card_ref chain resolution.
    The target card is re-read separately with round-trip YAML for
    writeback; the two loaders never share data.
    """
    cards = {}
    for card_path in CARDS_DIR.glob("*.md"):
        try:
            raw = card_path.read_text()
        except OSError:
            continue
        if not raw.startswith("---\n"):
            continue
        end = raw.find("\n---\n", 4)
        if end == -1:
            continue
        fm_text = raw[4 : end + 1]
        try:
            data = yaml_safe.load(io.StringIO(fm_text)) or {}
        except Exception:
            continue
        if isinstance(data, dict):
            cards[card_path.stem] = data
    return cards


def get_published_entry(data: dict, platform: str) -> dict | None:
    for entry in data.get("card_published") or []:
        if isinstance(entry, dict) and entry.get("platform") == platform:
            return entry
    return None


def find_thread_root(start_uuid: str, all_cards: dict) -> str:
    """Walk card_reply_to from start_uuid to the topmost ancestor.

    Returns the UUID of the thread root (the card with no card_reply_to).
    Detects cycles via a seen set and fails loudly.
    """
    seen: set[str] = set()
    current = start_uuid
    while True:
        if current in seen:
            raise SystemExit(
                f"error: cycle detected in card_reply_to chain at {current}"
            )
        seen.add(current)
        card = all_cards.get(current)
        if card is None:
            raise SystemExit(
                f"error: card {current} missing (walking reply chain)"
            )
        next_parent = card.get("card_reply_to")
        if not next_parent:
            return current
        current = next_parent


def resolve_reply(
    data: dict, all_cards: dict, platform: str
) -> tuple[dict | None, dict | None]:
    """Return (parent_entry, root_entry) from card_published[] lookups.

    Both are None if the target has no card_reply_to. For direct replies
    to a thread root, parent_entry and root_entry are the SAME object.
    Raises SystemExit if the chain cannot be fully resolved on `platform`.
    """
    parent_uuid = data.get("card_reply_to")
    if not parent_uuid:
        return None, None

    parent = all_cards.get(parent_uuid)
    if parent is None:
        raise SystemExit(
            f"error: card_reply_to={parent_uuid} — parent card file missing"
        )
    parent_entry = get_published_entry(parent, platform)
    if parent_entry is None:
        raise SystemExit(
            f"error: parent card {parent_uuid} is not yet on {platform}. "
            "Publish the parent first."
        )

    root_uuid = find_thread_root(parent_uuid, all_cards)
    if root_uuid == parent_uuid:
        # Direct reply to a root post: parent IS the thread root.
        return parent_entry, parent_entry

    root_card = all_cards[root_uuid]
    root_entry = get_published_entry(root_card, platform)
    if root_entry is None:
        raise SystemExit(
            f"error: thread root {root_uuid} is not yet on {platform}. "
            "Publish the root first."
        )
    return parent_entry, root_entry


def resolve_ref(data: dict, all_cards: dict, platform: str) -> dict | None:
    """Return the card_ref target's card_published[] entry, or None."""
    ref_uuid = data.get("card_ref")
    if not ref_uuid:
        return None

    ref_card = all_cards.get(ref_uuid)
    if ref_card is None:
        raise SystemExit(
            f"error: card_ref={ref_uuid} — referenced card file missing"
        )
    ref_entry = get_published_entry(ref_card, platform)
    if ref_entry is None:
        raise SystemExit(
            f"error: referenced card {ref_uuid} is not yet on {platform}. "
            "Publish the ref target first."
        )
    return ref_entry


def build_platform_args(
    platform: str,
    parent_entry: dict | None,
    root_entry: dict | None,
    ref_entry: dict | None,
    bib_data: dict | None,
    bib_body: str,
) -> list[str]:
    """Translate resolved card_published[] entries into platform CLI args."""
    if platform != "bluesky":
        raise SystemExit(
            f"error: no link-argument translation defined for platform {platform}"
        )

    args: list[str] = []
    if parent_entry:
        args += [
            "--reply-to-uri", parent_entry["id"],
            "--reply-to-cid", parent_entry["cid"],
        ]
    # Only pass --root-* when parent and root are different cards. For
    # direct replies to a root, bluesky.py defaults root = parent.
    if (
        parent_entry
        and root_entry
        and root_entry.get("id") != parent_entry.get("id")
    ):
        args += [
            "--root-uri", root_entry["id"],
            "--root-cid", root_entry["cid"],
        ]
    if ref_entry:
        args += [
            "--quote-uri", ref_entry["id"],
            "--quote-cid", ref_entry["cid"],
        ]
    # Literature cards: use the bib entry to build an external link
    # preview card. Skip silently if the card has no bib, if bib_url is
    # missing, or if the card already carries a quote (record+external
    # needs recordWithMedia; bluesky.py refuses that combo anyway).
    if bib_data and not ref_entry:
        bib_url = bib_data.get("bib_url")
        if bib_url:
            title = (bib_data.get("bib_title") or "").strip() or bib_url
            description = ""
            if bib_body:
                description = bib_body.split("\n\n", 1)[0].strip()
                if len(description) > 300:
                    description = description[:299] + "…"
            args += ["--embed-uri", bib_url, "--embed-title", title]
            if description:
                args += ["--embed-description", description]
    return args


def auto_commit(card_path: Path, body_stripped: str, platforms: list[str]) -> None:
    """Stage and commit the updated card file in the content/ git repo.

    Runs `git -C content add <rel> && git -C content commit -m ...` with
    a message built from a body preview and the list of platforms that
    were just published. No-op if content/ is not a git working tree.
    Failures are reported but do not overwrite the successful publish.
    """
    git_dir = CONTENT_DIR / ".git"
    if not git_dir.exists():
        sys.stderr.write(
            f"warning: {CONTENT_DIR} is not a git working tree; "
            "skipping auto-commit\n"
        )
        return

    try:
        rel_path = card_path.relative_to(CONTENT_DIR)
    except ValueError:
        sys.stderr.write(
            f"warning: card {card_path} is outside {CONTENT_DIR}; "
            "skipping auto-commit\n"
        )
        return

    preview = body_stripped.replace("\n", " ").strip()
    if len(preview) > 72:
        preview = preview[:71] + "…"
    plat_str = ",".join(platforms)
    message = f"publish: {plat_str}: {preview}"

    try:
        subprocess.run(
            ["git", "-C", str(CONTENT_DIR), "add", str(rel_path)],
            check=True,
            capture_output=True,
            text=True,
        )
        subprocess.run(
            ["git", "-C", str(CONTENT_DIR), "commit", "-m", message],
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as e:
        sys.stderr.write(
            f"warning: auto-commit failed ({e.returncode}): "
            f"{e.stderr or e.stdout}\n"
        )
        sys.stderr.write(
            "The card file has been updated on disk; commit it manually.\n"
        )
        return

    print(f"committed: {rel_path} ({message})")


def call_publisher(platform: str, text: str, extra_args: list[str]) -> dict:
    """Run publishers/<platform>.sh and parse its JSON stdout line."""
    script = PUBLISHERS_DIR / f"{platform}.sh"
    if not script.exists():
        raise SystemExit(f"error: no publisher wrapper at {script}")

    cmd = [str(script), "--text", text] + extra_args
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        sys.stderr.write(result.stderr)
        raise SystemExit(
            f"error: {platform} publisher exited {result.returncode}"
        )

    lines = [ln for ln in result.stdout.splitlines() if ln.strip()]
    if not lines:
        sys.stderr.write(result.stderr)
        raise SystemExit(f"error: {platform} publisher returned no output")

    try:
        return json.loads(lines[-1])
    except json.JSONDecodeError as e:
        sys.stderr.write(result.stdout)
        sys.stderr.write(result.stderr)
        raise SystemExit(
            f"error: could not parse {platform} publisher output: {e}"
        )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Publish a card to all configured platforms."
    )
    parser.add_argument("--card", required=True, metavar="UUID")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the plan; do not call platform scripts or write files.",
    )
    parser.add_argument(
        "--no-commit",
        action="store_true",
        help=(
            "Skip the git auto-commit of the updated card file. "
            "By default, a successful publish stages and commits the "
            "card in the content/ repo with message "
            "'publish: <body preview>'."
        ),
    )
    args = parser.parse_args()

    card_path = CARDS_DIR / f"{args.card}.md"
    if not card_path.exists():
        raise SystemExit(f"error: card not found: {card_path}")

    raw = card_path.read_text()
    fm_text, body = split_frontmatter(raw)
    data = yaml_rt.load(io.StringIO(fm_text)) or {}
    body_stripped = body.strip()

    body_len = count_chars(body_stripped)
    if body_len > LIMIT:
        raise SystemExit(
            f"error: card over limit (body={body_len}, limit={LIMIT})"
        )

    all_cards = load_all_cards()

    bib_data: dict | None = None
    bib_body: str = ""
    bib_uuid = data.get("card_bib")
    if bib_uuid:
        bib_data, bib_body = load_bib(bib_uuid)

    already = data.get("card_published") or []
    already_platforms = {
        entry.get("platform") for entry in already if hasattr(entry, "get")
    }

    targets = [p for p in PLATFORMS if p not in already_platforms]
    skipped = [p for p in PLATFORMS if p in already_platforms]

    # Resolve the link graph for EVERY target up front. This surfaces
    # blocker errors (missing parent, unresolved ref) before any network
    # call, so a partial publish never leaves the card in a weird state.
    plan: list[
        tuple[str, dict | None, dict | None, dict | None, list[str]]
    ] = []
    for platform in targets:
        parent_entry, root_entry = resolve_reply(data, all_cards, platform)
        ref_entry = resolve_ref(data, all_cards, platform)
        extra_args = build_platform_args(
            platform, parent_entry, root_entry, ref_entry, bib_data, bib_body
        )
        plan.append((platform, parent_entry, root_entry, ref_entry, extra_args))

    reply_to = data.get("card_reply_to")
    ref = data.get("card_ref")

    print(f"card:     {args.card}")
    print(f"chars:    body={body_len} limit={LIMIT}")
    if reply_to:
        print(f"reply_to: {reply_to}")
    if ref:
        print(f"card_ref: {ref}")
    print("--- post ---")
    print(body_stripped)
    print("--- end ----")
    print(f"targets:  {', '.join(targets) if targets else '<none>'}")
    if skipped:
        print(f"skipped:  {', '.join(skipped)} (already published)")

    for platform, parent_entry, root_entry, ref_entry, extra_args in plan:
        if parent_entry:
            print(f"  {platform}: parent = {parent_entry['id']}")
            if (
                root_entry
                and root_entry.get("id") != parent_entry.get("id")
            ):
                print(f"  {platform}: root   = {root_entry['id']}")
        if ref_entry:
            print(f"  {platform}: quote  = {ref_entry['id']}")
        if "--embed-uri" in extra_args:
            i = extra_args.index("--embed-uri")
            print(f"  {platform}: embed  = {extra_args[i + 1]}")

    if not targets:
        print("nothing to do: all configured platforms already published.")
        return

    if args.dry_run:
        print("dry-run: would call:")
        for platform, _, _, _, extra_args in plan:
            arg_str = " ".join(extra_args)
            print(f"  {PUBLISHERS_DIR / f'{platform}.sh'} --text <body> {arg_str}")
        print("dry-run: no subprocess calls, no file write")
        return

    new_entries = []
    for platform, _, _, _, extra_args in plan:
        print(f"-> publishing to {platform}...")
        result = call_publisher(platform, body_stripped, extra_args)
        # ISO 8601 UTC, millisecond precision, matching existing Twitter
        # entries in the codebase. This is the actual publish moment,
        # not card_created — useful for cards that sit in the queue
        # before being posted.
        now_iso = (
            datetime.now(timezone.utc)
            .isoformat(timespec="milliseconds")
            .replace("+00:00", "Z")
        )
        entry = {"platform": platform, "id": result["id"]}
        if result.get("cid"):
            entry["cid"] = result["cid"]
        entry["date"] = now_iso
        new_entries.append(entry)
        print(f"   id={entry['id']}")
        if entry.get("cid"):
            print(f"   cid={entry['cid']}")
        print(f"   date={entry['date']}")

    if data.get("card_published"):
        for entry in new_entries:
            data["card_published"].append(entry)
    else:
        data["card_published"] = new_entries

    buf = io.StringIO()
    yaml_rt.dump(data, buf)
    card_path.write_text(assemble(buf.getvalue(), body))
    print(f"updated:  {card_path.relative_to(ROOT)}")

    if not args.no_commit:
        published_platforms = [e["platform"] for e in new_entries]
        auto_commit(card_path, body_stripped, published_platforms)


if __name__ == "__main__":
    main()
