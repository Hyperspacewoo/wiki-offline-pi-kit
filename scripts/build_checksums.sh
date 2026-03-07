#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$ROOT_DIR"
find . -type f \
  ! -path './.git/*' \
  ! -path './config/checksums.txt' \
  -print0 | sort -z | xargs -0 sha256sum > ./config/checksums.txt
echo "Wrote config/checksums.txt"
