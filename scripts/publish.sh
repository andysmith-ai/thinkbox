#!/usr/bin/env bash
# Card publish wrapper: runs publish.py (the card fan-out orchestrator)
# under nix-shell with the minimum dependencies it needs.
#
# publish.py shells out to thinkbox/scripts/publishers/<platform>.sh for
# each target platform, so platform-specific deps (and credentials) live
# in those per-platform wrappers — NOT here.
#
# Usage:
#   ./thinkbox/scripts/publish.sh --card <uuid>
#   ./thinkbox/scripts/publish.sh --card <uuid> --dry-run
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PUBLISH_PY="$SCRIPT_DIR/publish.py"

# Build properly escaped command string for nix-shell --run
CMD="python3 $(printf '%q' "$PUBLISH_PY")"
for arg in "$@"; do
  CMD="$CMD $(printf '%q' "$arg")"
done

exec nix-shell -p "python3.withPackages(ps: [ps.ruamel-yaml])" --run "$CMD"
