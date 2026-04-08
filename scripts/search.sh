#!/usr/bin/env bash
# Wrapper: sources secrets from .env and runs search.py
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
SEARCH_PY="$SCRIPT_DIR/../src/thinkbox_search/search.py"

set -a
source "$ROOT/.env"
set +a

# Build properly escaped command string for nix-shell --run
CMD="python3 $(printf '%q' "$SEARCH_PY") -d $(printf '%q' "$ROOT/content")"
for arg in "$@"; do
  CMD="$CMD $(printf '%q' "$arg")"
done

exec nix-shell -p "python3.withPackages(ps: [ps.pyyaml ps.qdrant-client])" \
  --keep OPENROUTER_API_KEY --keep QDRANT_URL --keep QDRANT_API_KEY \
  --run "$CMD"
