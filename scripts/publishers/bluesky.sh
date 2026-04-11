#!/usr/bin/env bash
# Standalone Bluesky publisher wrapper.
# Sources .env and runs bluesky.py in a nix-shell with atproto available.
#
# Usage:
#   ./thinkbox/scripts/publishers/bluesky.sh --text "Hello, Bluesky."
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
BLUESKY_PY="$SCRIPT_DIR/bluesky.py"

set -a
source "$ROOT/.env"
set +a

# Build properly escaped command string for nix-shell --run
CMD="python3 $(printf '%q' "$BLUESKY_PY")"
for arg in "$@"; do
  CMD="$CMD $(printf '%q' "$arg")"
done

exec nix-shell -p "python3.withPackages(ps: [ps.atproto])" \
  --keep BLUESKY_HANDLE --keep BLUESKY_APP_PASSWORD \
  --run "$CMD"
