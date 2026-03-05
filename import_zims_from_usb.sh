#!/usr/bin/env bash
set -euo pipefail
SRC="${1:-}"
DST="${2:-$HOME/wiki/zim}"
if [[ -z "$SRC" || ! -d "$SRC" ]]; then
  echo "Usage: $0 /path/to/usb_or_folder_with_zims [dest_folder]"
  exit 1
fi
mkdir -p "$DST"
find "$SRC" -type f -iname '*.zim' -print0 | while IFS= read -r -d '' f; do
  echo "Copying: $f"
  cp -n "$f" "$DST/"
done
echo "Done. Re-open dashboard and click Rescan + Sync All ZIMs."
