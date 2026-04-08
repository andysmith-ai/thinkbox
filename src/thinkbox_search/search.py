#!/usr/bin/env python3
"""Semantic search over content via Qdrant + OpenRouter embeddings."""

import json
import os
import ssl
import urllib.request
from pathlib import Path

EMBEDDING_MODEL = "qwen/qwen3-embedding-8b"
COLLECTION_NAME = "content"

OPENROUTER_API_KEY = os.environ["OPENROUTER_API_KEY"]
QDRANT_URL = os.environ["QDRANT_URL"]
QDRANT_API_KEY = os.environ["QDRANT_API_KEY"]


def embed(text: str) -> list[float]:
    body = json.dumps({"model": EMBEDDING_MODEL, "input": [text]}).encode()
    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/embeddings",
        data=body,
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
        },
    )
    ctx = ssl.create_default_context()
    with urllib.request.urlopen(req, context=ctx) as resp:
        data = json.loads(resp.read())
    return data["data"][0]["embedding"]


def _qdrant_post(path: str, payload: dict) -> dict:
    body = json.dumps(payload).encode()
    req = urllib.request.Request(
        f"{QDRANT_URL}{path}",
        data=body,
        headers={
            "Content-Type": "application/json",
            "api-key": QDRANT_API_KEY,
        },
    )
    ctx = ssl.create_default_context()
    try:
        with urllib.request.urlopen(req, context=ctx) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        err_body = e.read().decode()
        raise RuntimeError(f"Qdrant {e.code}: {err_body}") from e


def search(query: str, limit: int = 10, type_filter: str | None = None) -> list[dict]:
    vector = embed(query)
    payload: dict = {
        "vector": vector,
        "limit": limit,
        "with_payload": True,
    }
    if type_filter:
        payload["filter"] = {
            "must": [{"key": "type", "match": {"value": type_filter}}]
        }
    data = _qdrant_post(f"/collections/{COLLECTION_NAME}/points/search", payload)
    return data["result"]


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Semantic search over content")
    parser.add_argument("query", help="Search query")
    parser.add_argument("-n", "--limit", type=int, default=10, help="Max results")
    parser.add_argument("-t", "--type", help="Filter by type: wiki, x, bib, blog")
    parser.add_argument(
        "-d", "--content-dir",
        default=".",
        help="Path to content/ directory (default: cwd)",
    )
    args = parser.parse_args()

    content_root = Path(args.content_dir).resolve()
    results = search(args.query, args.limit, args.type)
    for r in results:
        p = r["payload"]
        score = r["score"]
        path = p.get("path", "?")
        title = p.get("title") or p.get("bib_title") or ""
        header = f"{score:.3f}  {path}"
        if title:
            header += f"  — {title}"
        print(header)
        # Print file content
        filepath = content_root / path
        if filepath.exists():
            text = filepath.read_text(encoding="utf-8").strip()
            for line in text.split("\n"):
                print(f"  {line}")
        print()


if __name__ == "__main__":
    main()
