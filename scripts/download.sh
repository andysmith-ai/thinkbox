#!/usr/bin/env bash
# Download a source and convert to clean markdown.
# Usage: download.sh <uuid> <url>
# Creates artifacts/{uuid}/ with original.md and original.tar.gz
set -euo pipefail

UUID="$1"
URL="$2"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
ARTIFACT_DIR="$ROOT/artifacts/$UUID"

mkdir -p "$ARTIFACT_DIR"
cd "$ARTIFACT_DIR"

# Download
nix-shell -p wget --run "wget -p -k -nH --no-parent '$URL' -P raw"

# Find the main HTML file (try common patterns)
HTML_FILE=$(find raw -name '*.html' -o -name '*.htm' | head -1)
if [ -z "$HTML_FILE" ]; then
  URL_PATH=$(echo "$URL" | sed 's|https\?://[^/]*/||')
  if [ -f "raw/$URL_PATH" ]; then
    HTML_FILE="raw/$URL_PATH"
  elif [ -f "raw/${URL_PATH}/index.html" ]; then
    HTML_FILE="raw/${URL_PATH}/index.html"
  else
    HTML_FILE=$(find raw -type f -not -name '*.css' -not -name '*.js' \
      -not -name '*.png' -not -name '*.jpg' -not -name '*.gif' \
      -not -name '*.svg' -not -name '*.webp' -not -name '*.woff*' \
      -not -name '*.ttf' -not -name '*.ico' \
      -exec ls -S {} + 2>/dev/null | head -1)
  fi
fi

if [ -z "$HTML_FILE" ]; then
  echo "ERROR: Could not find HTML file in download" >&2
  exit 1
fi

echo "Converting: $HTML_FILE"

# Convert to clean markdown (preserves links, images, structure)
nix-shell -p pandoc --run "pandoc '$HTML_FILE' -f html -t markdown --wrap=none -o original.md"

# Archive and clean up
tar czf original.tar.gz raw
rm -rf raw

echo "Done: $ARTIFACT_DIR"
echo "  original.md: $(wc -c < original.md) bytes"
echo "  original.tar.gz: $(wc -c < original.tar.gz) bytes"
