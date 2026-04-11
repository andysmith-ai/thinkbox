#!/usr/bin/env bash
# Wrapper: runs queue.py under a nix-shell with ruamel-yaml.
#
# queue.py is read-only — no credentials needed, no network calls, no
# file writes. It just reads content/cards/*.md and prints the queue
# for the requested platform.
#
# Usage:
#   ./thinkbox/scripts/queue.sh bluesky
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
QUEUE_PY="$SCRIPT_DIR/queue.py"

CMD="python3 $(printf '%q' "$QUEUE_PY")"
for arg in "$@"; do
  CMD="$CMD $(printf '%q' "$arg")"
done

exec nix-shell -p "python3.withPackages(ps: [ps.ruamel-yaml])" --run "$CMD"
