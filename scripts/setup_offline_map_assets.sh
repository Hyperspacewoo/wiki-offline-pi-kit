#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=/dev/null
source "${SCRIPT_DIR}/layout.sh"

MAP_ROOT="${WIKI_MAPS_DIR}"
STATIC_DIR="${MAP_ROOT}/static"
DATA_DIR="${MAP_ROOT}/data"

mkdir -p "$STATIC_DIR" "$DATA_DIR"

copy_or_fetch() {
  local name="$1"
  local url="$2"
  local src="${MAP_ASSETS_DIR}/${name}"
  local dst="${STATIC_DIR}/${name}"

  if [[ -f "$src" ]]; then
    cp -f "$src" "$dst"
    echo "Copied offline map asset: $name"
    return 0
  fi

  if [[ "${OFFLINE_ONLY}" == "1" ]]; then
    echo "OFFLINE_ONLY=1 and missing map asset: $src" >&2
    return 1
  fi

  curl -L -o "$dst" "$url"
  echo "Downloaded map asset: $name"
}

# Local JS/CSS for offline map UI (no CDN dependency at runtime)
copy_or_fetch maplibre-gl.js https://unpkg.com/maplibre-gl@5.9.0/dist/maplibre-gl.js
copy_or_fetch maplibre-gl.css https://unpkg.com/maplibre-gl@5.9.0/dist/maplibre-gl.css
copy_or_fetch pmtiles.js https://unpkg.com/pmtiles@4.4.0/dist/pmtiles.js

echo "Map UI assets ready at: $STATIC_DIR"
