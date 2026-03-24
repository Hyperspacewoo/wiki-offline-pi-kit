#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=/dev/null
source "${SCRIPT_DIR}/layout.sh"

MAP_ROOT="${WIKI_MAPS_DIR}"
STATIC_DIR="${MAP_ROOT}/static"
DATA_DIR="${MAP_ROOT}/data"

mkdir -p "$STATIC_DIR" "$DATA_DIR"

# Local JS/CSS for offline map UI (no CDN dependency at runtime)
curl -L -o "$STATIC_DIR/maplibre-gl.js" https://unpkg.com/maplibre-gl@5.9.0/dist/maplibre-gl.js
curl -L -o "$STATIC_DIR/maplibre-gl.css" https://unpkg.com/maplibre-gl@5.9.0/dist/maplibre-gl.css
curl -L -o "$STATIC_DIR/pmtiles.js" https://unpkg.com/pmtiles@4.4.0/dist/pmtiles.js

echo "Downloaded map UI assets to: $STATIC_DIR"
