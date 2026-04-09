#!/usr/bin/env bash
# Archive a cloned repo and clean up working files.
# Usage: archive-repo.sh <uuid>
# Replaces repo/ and tree.txt with original.tar.gz
set -euo pipefail

UUID="$1"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
ARTIFACT_DIR="$ROOT/artifacts/$UUID"

cd "$ARTIFACT_DIR"

tar czf original.tar.gz --exclude='.git' repo
rm -rf repo tree.txt

echo "Archived: $ARTIFACT_DIR"
echo "  original.tar.gz: $(wc -c < original.tar.gz) bytes"
