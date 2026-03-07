#!/usr/bin/env bash
set -euo pipefail
TARGET="${1:-}"
if [[ -z "$TARGET" || ! -d "$TARGET" ]]; then
  echo "Usage: $0 /path/to/usb_mount"
  exit 1
fi
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
mkdir -p "$TARGET/OffgridIntelKit"
rsync -a --exclude='.git' "$ROOT_DIR/" "$TARGET/OffgridIntelKit/wiki-offline-pi-kit/"
cp -f "$ROOT_DIR/INSTALL_OFFLINE_KNOWLEDGE.sh" "$TARGET/" || true
cp -f "$ROOT_DIR/docs/START_HERE.txt" "$TARGET/" || true
echo "Bundle exported to $TARGET"
