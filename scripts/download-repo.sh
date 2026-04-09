#!/usr/bin/env bash
# Download a GitHub repo and create initial artifacts.
# Usage: download-repo.sh <uuid> <github-url>
# Creates artifacts/{uuid}/ with repo/, original.txt, links.csv
set -euo pipefail

UUID="$1"
URL="$2"

# Extract owner/repo from URL
OWNER_REPO=$(echo "$URL" | sed 's|https://github.com/||' | sed 's|\.git$||' | sed 's|/$||')

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
ARTIFACT_DIR="$ROOT/artifacts/$UUID"

mkdir -p "$ARTIFACT_DIR"
cd "$ARTIFACT_DIR"

# Clone (shallow)
nix-shell -p git --run "git clone --depth 1 '$URL' repo"

# Generate file tree (excluding noise)
find repo -type f \
  \( -path '*/.git/*' -o -path '*/node_modules/*' -o -path '*/dist/*' \
  -o -path '*/build/*' -o -path '*/vendor/*' -o -path '*/__pycache__/*' \
  -o -path '*/.venv/*' -o -path '*/target/*' \) -prune \
  -o -type f -print | sort > tree.txt

# Scaffold original.txt
{
  echo "=== REPO: $OWNER_REPO ==="
  echo "URL: $URL"
  echo "Cloned: $(date -Iseconds)"
  echo "Commit: $(cd repo && git rev-parse HEAD)"
  echo ""
  echo "=== FILE TREE ==="
  cat tree.txt
  echo ""
  echo "=== README ==="
  cat repo/README.md 2>/dev/null || cat repo/readme.md 2>/dev/null || echo "(no README)"
} > original.txt

# Extract links from README
nix-shell -p python3 --run "python3 -c \"
import os, re, csv
links = []
for root, dirs, files in os.walk('repo'):
    dirs[:] = [d for d in dirs if d not in ('.git','node_modules','dist','build','vendor','__pycache__','.venv','target')]
    for f in files:
        if f.lower().startswith('readme'):
            with open(os.path.join(root,f)) as fh:
                for m in re.finditer(r'\[([^\]]*)\]\(([^)]+)\)', fh.read()):
                    if m.group(2).startswith(('http://','https://')):
                        links.append((m.group(1), m.group(2)))
with open('links.csv','w',newline='') as f:
    csv.writer(f).writerows(links)
\""

echo "Done: $ARTIFACT_DIR"
echo "  original.txt: $(wc -c < original.txt) bytes"
echo "  links.csv: $(wc -c < links.csv) bytes"
echo "  repo/ cloned"
