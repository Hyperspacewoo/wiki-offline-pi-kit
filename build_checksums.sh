#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
find . -type f \
  ! -name 'checksums.txt' \
  ! -path './.git/*' \
  -print0 | sort -z | xargs -0 sha256sum > checksums.txt
echo "Wrote checksums.txt"
