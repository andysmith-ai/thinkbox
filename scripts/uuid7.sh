#!/usr/bin/env bash
# Generate a UUID v7
set -euo pipefail
exec nix-shell -p "python3.withPackages(ps: [ps.uuid-utils])" \
  --run "python3 -c \"import uuid_utils; print(uuid_utils.uuid7())\""
