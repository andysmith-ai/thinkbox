#!/usr/bin/env python3
"""Print the queue of cards waiting to be published to a given platform.

A card is in the queue for platform X if its `card_published[]` does NOT
yet contain an entry with platform=X. Every card is a publishing
candidate for every platform by default — there is no opt-in field.

This is a REPORT, not a publish instruction. One line per card:

  <indent><↵?><uuid>  [status]  <body preview>   [→ <ref_uuid>]

  - Top-level cards start at column 0
  - Reply cards are indented 2 spaces per depth and prefixed with ↵
  - Cards with a `card_ref` show a trailing → <ref_uuid>
  - [ready]   — no unresolved dependencies
  - [blocked] — a `card_reply_to` or `card_ref` target is not yet on X

Readable by humans (visual tree) and by machines (fixed UUID + tag
layout per line, greppable).

Usage:
  queue.py <platform>

Example:
  queue.py bluesky
"""

import argparse
import io
import sys
from pathlib import Path

from ruamel.yaml import YAML

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent.parent  # thinkbox/scripts -> thinkbox -> repo root
CARDS_DIR = ROOT / "content" / "cards"

yaml = YAML(typ="safe")  # read-only; no round-trip needed


def split_frontmatter(text: str) -> tuple[str, str]:
    if not text.startswith("---\n"):
        return "", text
    end = text.find("\n---\n", 4)
    if end == -1:
        return "", text
    return text[4 : end + 1], text[end + len("\n---\n") :]


def load_cards() -> dict:
    """Return {uuid: (path, frontmatter_dict, body_stripped)}."""
    cards = {}
    for card_path in sorted(CARDS_DIR.glob("*.md")):
        try:
            raw = card_path.read_text()
        except OSError as e:
            sys.stderr.write(f"warn: could not read {card_path.name}: {e}\n")
            continue
        fm_text, body = split_frontmatter(raw)
        if not fm_text:
            continue
        try:
            data = yaml.load(io.StringIO(fm_text)) or {}
        except Exception as e:
            sys.stderr.write(f"warn: could not parse {card_path.name}: {e}\n")
            continue
        if not isinstance(data, dict):
            continue
        cards[card_path.stem] = (card_path, data, body.strip())
    return cards


def is_published_to(data: dict, platform: str) -> bool:
    for entry in data.get("card_published") or []:
        if isinstance(entry, dict) and entry.get("platform") == platform:
            return True
    return False


def dep_blocker(
    dep_uuid: str, dep_field: str, platform: str, all_cards: dict
) -> str | None:
    """Return a human-readable blocker reason, or None if the dep is satisfied."""
    dep = all_cards.get(dep_uuid)
    if dep is None:
        return f"{dep_field}={dep_uuid[:8]}... (card file missing)"
    _, dep_data, _ = dep
    if is_published_to(dep_data, platform):
        return None
    return f"{dep_field}={dep_uuid[:8]}... (not yet on {platform})"


def preview(body: str, width: int) -> str:
    flat = body.replace("\n", " ").strip()
    if len(flat) <= width:
        return flat
    return flat[: max(1, width - 1)] + "…"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Print the queue of cards waiting to be published to a platform."
    )
    parser.add_argument(
        "platform",
        help="Target platform (e.g. bluesky). Checked against card_published entries.",
    )
    args = parser.parse_args()
    platform = args.platform

    all_cards = load_cards()

    # Queue = every card not yet published to the target platform.
    # No opt-in field: every card is a candidate for every platform.
    queue = {
        uuid: (path, data, body)
        for uuid, (path, data, body) in all_cards.items()
        if not is_published_to(data, platform)
    }

    if not queue:
        print(f"queue [{platform}]: empty — all cards already published")
        return

    # Per-card status (ready / blocked, with blocker reasons).
    statuses: dict[str, tuple[str, list[str]]] = {}
    ready_count = 0
    blocked_count = 0
    for uuid, (_, data, _) in queue.items():
        blockers: list[str] = []
        reply_to = data.get("card_reply_to")
        ref = data.get("card_ref")
        if reply_to:
            b = dep_blocker(reply_to, "card_reply_to", platform, all_cards)
            if b:
                blockers.append(b)
        if ref:
            b = dep_blocker(ref, "card_ref", platform, all_cards)
            if b:
                blockers.append(b)
        if blockers:
            statuses[uuid] = ("blocked", blockers)
            blocked_count += 1
        else:
            statuses[uuid] = ("ready", [])
            ready_count += 1

    # Build the reply tree: a card is nested under its card_reply_to parent
    # only if that parent is also in the queue. Otherwise the card is
    # top-level (the parent is already published, or missing entirely).
    children_of: dict[str, list[str]] = {}
    top_level: list[str] = []
    for uuid, (_, data, _) in queue.items():
        parent = data.get("card_reply_to")
        if parent and parent in queue:
            children_of.setdefault(parent, []).append(uuid)
        else:
            top_level.append(uuid)

    def created_key(uuid: str) -> str:
        return str(queue[uuid][1].get("card_created") or "")

    top_level.sort(key=created_key)
    for parent_uuid in children_of:
        children_of[parent_uuid].sort(key=created_key)

    print(
        f"queue [{platform}]: {len(queue)} card(s) — "
        f"{ready_count} ready, {blocked_count} blocked"
    )
    print()

    def render(uuid: str, depth: int) -> None:
        _, data, body = queue[uuid]
        status_kind, _ = statuses[uuid]
        status_str = f"[{status_kind}]"

        indent = "  " * depth
        marker = "↵ " if depth > 0 else ""

        ref = data.get("card_ref")
        trailing = f"   → {ref}" if ref else ""

        # Budget: total line ≤ 120 cols. Preview fills what's left.
        # Overhead = indent + marker + uuid + 2 spaces + status + trailing
        overhead = len(indent) + len(marker) + 36 + 2 + len(status_str) + len(trailing)
        avail = max(20, 120 - overhead - 2)  # 2 spaces between status and preview
        snippet = preview(body, avail)

        print(f"{indent}{marker}{uuid}  {status_str}  {snippet}{trailing}")

        for child_uuid in children_of.get(uuid, []):
            render(child_uuid, depth + 1)

    for uuid in top_level:
        render(uuid, 0)


if __name__ == "__main__":
    main()
