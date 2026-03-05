#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
if [[ ! -f checksums.txt ]]; then
  echo "checksums.txt not found. Run ./build_checksums.sh first."
  exit 1
fi
sha256sum -c checksums.txt
