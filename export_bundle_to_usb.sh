#!/usr/bin/env bash
set -euo pipefail
TARGET="${1:-}"
if [[ -z "$TARGET" || ! -d "$TARGET" ]]; then
  echo "Usage: $0 /path/to/usb_mount"
  exit 1
fi
mkdir -p "$TARGET/OfflineKnowledgeKit"
rsync -a --exclude='.git' ./ "$TARGET/OfflineKnowledgeKit/wiki-offline-pi-kit/"
cp -f INSTALL_OFFLINE_KNOWLEDGE.sh "$TARGET/" || true
cp -f START_HERE.txt "$TARGET/" || true
echo "Bundle exported to $TARGET"
