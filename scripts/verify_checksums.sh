#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$ROOT_DIR"
if [[ ! -f ./config/checksums.txt ]]; then
  echo "config/checksums.txt not found. Run ./scripts/build_checksums.sh first."
  exit 1
fi
sha256sum -c ./config/checksums.txt
