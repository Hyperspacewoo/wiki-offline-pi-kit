#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=/dev/null
source "${SCRIPT_DIR}/layout.sh"

INCLUDE_TRANSLATOR=0
EXTRA_ITEMS=()
for arg in "$@"; do
  case "$arg" in
    --translator)
      INCLUDE_TRANSLATOR=1
      ;;
    *)
      EXTRA_ITEMS+=("$arg")
      ;;
  esac
done

mkdir -p \
  "$PYTHON_WHEELHOUSE" \
  "$MAP_ASSETS_DIR" \
  "$OFFLINE_DATASETS_DIR" \
  "$INSTALLER_BIN_DIR" \
  "$MAP_BUNDLES_DIR" \
  "$ARGOS_MODELS_DIR"

echo "== Fetching core Python wheelhouse =="
python3 -m pip download -r "${WIKI_KIT_ROOT}/requirements/core.txt" -d "$PYTHON_WHEELHOUSE"

if [[ "$INCLUDE_TRANSLATOR" == "1" ]]; then
  echo "== Fetching translator Python wheelhouse =="
  python3 -m pip download -r "${WIKI_KIT_ROOT}/requirements/translator.txt" -d "$PYTHON_WHEELHOUSE"
fi

echo "== Fetching map UI assets =="
curl -L -o "$MAP_ASSETS_DIR/maplibre-gl.js" https://unpkg.com/maplibre-gl@5.9.0/dist/maplibre-gl.js
curl -L -o "$MAP_ASSETS_DIR/maplibre-gl.css" https://unpkg.com/maplibre-gl@5.9.0/dist/maplibre-gl.css
curl -L -o "$MAP_ASSETS_DIR/pmtiles.js" https://unpkg.com/pmtiles@4.4.0/dist/pmtiles.js

echo "== Fetching GeoNames US place dataset =="
curl -L -o "$OFFLINE_DATASETS_DIR/US.zip" https://download.geonames.org/export/dump/US.zip

echo "== Fetching pmtiles CLI =="
TMP_TGZ="$(mktemp)"
curl -L -o "$TMP_TGZ" "https://github.com/protomaps/go-pmtiles/releases/download/v1.30.1/go-pmtiles_1.30.1_Linux_x86_64.tar.gz"
tar -xzf "$TMP_TGZ" -C "$INSTALLER_BIN_DIR" pmtiles
chmod +x "$INSTALLER_BIN_DIR/pmtiles"
rm -f "$TMP_TGZ"

echo "== Copying any user-supplied offline assets =="
for item in "${EXTRA_ITEMS[@]}"; do
  if [[ ! -e "$item" ]]; then
    echo "[WARN] Skipping missing path: $item"
    continue
  fi
  case "$item" in
    *.pmtiles)
      cp -f "$item" "$MAP_BUNDLES_DIR/"
      echo "Copied map dataset: $(basename "$item")"
      ;;
    *.argosmodel)
      cp -f "$item" "$ARGOS_MODELS_DIR/"
      echo "Copied Argos model: $(basename "$item")"
      ;;
    *)
      echo "[WARN] Unknown artifact type, skipped: $item"
      ;;
  esac
done

echo
echo "Bundle artifact fetch complete."
if [[ "$INCLUDE_TRANSLATOR" == "1" ]]; then
  echo "Translator wheel bundle requested. Expect a much larger wheelhouse because Argos pulls in heavy ML dependencies."
else
  echo "Translator wheels were skipped. Add --translator if you want fully offline translation dependencies too."
fi
echo "Still manual: installers/apt/*.deb (or keep apt internet available), plus any extra .pmtiles and .argosmodel files you want bundled."
