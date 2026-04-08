#!/usr/bin/env python3
"""Embed content markdown files into Qdrant via OpenRouter."""

import hashlib
import json
import os
import re
import ssl
import sys
import urllib.request
import uuid
from pathlib import Path

import yaml
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    PointStruct,
    VectorParams,
)

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
EMBEDDING_MODEL = "qwen/qwen3-embedding-8b"
COLLECTION_NAME = "content"
VECTOR_SIZE = 4096
CONTENT_DIRS = ["wiki", "x", "bib", "blog"]
EMBED_BATCH_SIZE = 32  # inputs per OpenRouter request
UUID_NAMESPACE = uuid.UUID("a1b2c3d4-e5f6-7890-abcd-ef1234567890")

OPENROUTER_API_KEY = os.environ["OPENROUTER_API_KEY"]
QDRANT_URL = os.environ["QDRANT_URL"]
QDRANT_API_KEY = os.environ["QDRANT_API_KEY"]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n?(.*)", re.DOTALL)


def parse_md(path: Path) -> tuple[dict, str]:
    """Return (frontmatter_dict, body) from a markdown file."""
    text = path.read_text(encoding="utf-8")
    m = FRONTMATTER_RE.match(text)
    if m:
        fm = yaml.safe_load(m.group(1)) or {}
        body = m.group(2)
    else:
        fm = {}
        body = text
    return fm, body


def file_hash(path: Path) -> str:
    """SHA-256 hex digest of file contents."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def point_id(rel_path: str) -> str:
    """Deterministic UUID5 from relative path."""
    return str(uuid.uuid5(UUID_NAMESPACE, rel_path))


def content_type(rel_path: str) -> str:
    """Return content type from first path segment."""
    return rel_path.split("/")[0]


def embed_text(fm: dict, body: str) -> str:
    """Build the text to embed: title (if any) + body."""
    title = fm.get("title") or fm.get("bib_title") or ""
    if title:
        return f"{title}\n\n{body}"
    return body


def build_payload(rel_path: str, fm: dict, hash_val: str) -> dict:
    """Build Qdrant point payload from frontmatter + metadata."""
    payload = {
        "path": rel_path,
        "type": content_type(rel_path),
        "content_hash": f"sha256:{hash_val}",
    }
    # Copy all frontmatter fields into payload
    for k, v in fm.items():
        if k == "software_version":
            continue
        # Convert dates/datetimes to ISO strings
        if hasattr(v, "isoformat"):
            v = v.isoformat()
        payload[k] = v
    return payload


# ---------------------------------------------------------------------------
# OpenRouter embedding API (stdlib only)
# ---------------------------------------------------------------------------
def call_openrouter_embed(texts: list[str]) -> list[list[float]]:
    """Call OpenRouter embeddings endpoint, return list of vectors."""
    url = "https://openrouter.ai/api/v1/embeddings"
    body = json.dumps({"model": EMBEDDING_MODEL, "input": texts}).encode()
    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
        },
    )
    ctx = ssl.create_default_context()
    with urllib.request.urlopen(req, context=ctx) as resp:
        data = json.loads(resp.read())
    # Sort by index to guarantee order
    data["data"].sort(key=lambda x: x["index"])
    return [d["embedding"] for d in data["data"]]


# ---------------------------------------------------------------------------
# Qdrant helpers
# ---------------------------------------------------------------------------
def ensure_collection(client: QdrantClient) -> None:
    """Create collection if it doesn't exist."""
    collections = [c.name for c in client.get_collections().collections]
    if COLLECTION_NAME not in collections:
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(
                size=VECTOR_SIZE, distance=Distance.COSINE
            ),
        )
        print(f"Created collection '{COLLECTION_NAME}'")
    # Ensure payload indexes exist
    for field, schema in [("type", "keyword"), ("tags", "keyword"), ("path", "keyword")]:
        client.create_payload_index(
            collection_name=COLLECTION_NAME,
            field_name=field,
            field_schema=schema,
        )


def scroll_all_points(client: QdrantClient) -> dict[str, str]:
    """Scroll all points, return {path: content_hash}."""
    remote = {}
    offset = None
    while True:
        results, next_offset = client.scroll(
            collection_name=COLLECTION_NAME,
            limit=256,
            offset=offset,
            with_payload=True,
            with_vectors=False,
        )
        for pt in results:
            p = pt.payload.get("path")
            h = pt.payload.get("content_hash", "")
            if p:
                remote[p] = h
        if next_offset is None:
            break
        offset = next_offset
    return remote


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Embed content into Qdrant")
    parser.add_argument(
        "content_root",
        nargs="?",
        default=".",
        help="Path to content/ directory (default: cwd)",
    )
    cli_args = parser.parse_args()
    content_root = Path(cli_args.content_root).resolve()

    # Discover local files
    local_files: dict[str, Path] = {}
    for d in CONTENT_DIRS:
        dir_path = content_root / d
        if not dir_path.is_dir():
            continue
        for md in dir_path.rglob("*.md"):
            rel = str(md.relative_to(content_root))
            local_files[rel] = md

    print(f"Found {len(local_files)} local markdown files")

    # Connect to Qdrant
    client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
    ensure_collection(client)
    remote = scroll_all_points(client)
    print(f"Found {len(remote)} existing points in Qdrant")

    # Diff
    to_upsert: list[str] = []  # rel paths
    for rel, path in local_files.items():
        h = f"sha256:{file_hash(path)}"
        if rel not in remote or remote[rel] != h:
            to_upsert.append(rel)

    to_delete = [p for p in remote if p not in local_files]

    unchanged = len(local_files) - len(to_upsert)
    print(
        f"Plan: {len(to_upsert)} upsert, {len(to_delete)} delete, "
        f"{unchanged} unchanged"
    )

    # Delete removed files
    if to_delete:
        ids = [point_id(p) for p in to_delete]
        client.delete(
            collection_name=COLLECTION_NAME,
            points_selector=ids,
        )
        print(f"Deleted {len(to_delete)} points")

    # Embed + upsert in batches
    upserted = 0
    for i in range(0, len(to_upsert), EMBED_BATCH_SIZE):
        batch_paths = to_upsert[i : i + EMBED_BATCH_SIZE]
        texts = []
        metas = []
        for rel in batch_paths:
            path = local_files[rel]
            fm, body = parse_md(path)
            texts.append(embed_text(fm, body))
            metas.append((rel, fm, file_hash(path)))

        vectors = call_openrouter_embed(texts)

        points = []
        for (rel, fm, h), vec in zip(metas, vectors):
            points.append(
                PointStruct(
                    id=point_id(rel),
                    vector=vec,
                    payload=build_payload(rel, fm, h),
                )
            )

        client.upsert(collection_name=COLLECTION_NAME, points=points)
        upserted += len(points)
        print(f"  Upserted batch {i // EMBED_BATCH_SIZE + 1}: {len(points)} points")

    print(
        f"\nDone: {upserted} added/updated, {len(to_delete)} deleted, "
        f"{unchanged} unchanged"
    )


if __name__ == "__main__":
    main()
