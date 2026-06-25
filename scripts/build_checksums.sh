#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$ROOT_DIR"

if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  git ls-files -z | grep -zv '^config/checksums.txt$' | xargs -0 sha256sum > ./config/checksums.txt
else
  find . -type f \
    ! -path './.git/*' \
    ! -path './offgrid-runtime/*' \
    ! -path './config/checksums.txt' \
    -print0 | sort -z | xargs -0 sha256sum > ./config/checksums.txt
fi
echo "Wrote config/checksums.txt"
