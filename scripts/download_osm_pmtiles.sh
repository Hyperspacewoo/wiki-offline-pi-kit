#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=/dev/null
source "${SCRIPT_DIR}/layout.sh"

# Defaults to NYC metro bbox and zoom suitable for laptop/Pi testing.
BBOX="${1:--74.30,40.45,-73.65,40.95}"
MAXZOOM="${2:-14}"
OUT="${3:-${WIKI_MAPS_DIR}/data/nyc.pmtiles}"
SRC="${4:-https://data.source.coop/protomaps/openstreetmap/v4.pmtiles}"

mkdir -p "$(dirname "$OUT")" "${WIKI_RUNTIME_ROOT}/bin"

PMTILES_BIN="${WIKI_RUNTIME_ROOT}/bin/pmtiles"
if [[ ! -x "$PMTILES_BIN" && -x "${INSTALLER_BIN_DIR}/pmtiles" ]]; then
  cp -f "${INSTALLER_BIN_DIR}/pmtiles" "$PMTILES_BIN"
  chmod +x "$PMTILES_BIN"
fi

if [[ ! -x "$PMTILES_BIN" ]]; then
  if [[ "${OFFLINE_ONLY}" == "1" ]]; then
    echo "OFFLINE_ONLY=1 and missing pmtiles CLI at ${INSTALLER_BIN_DIR}/pmtiles" >&2
    exit 1
  fi
  echo "Downloading pmtiles CLI..."
  TMP_TGZ="$(mktemp)"
  curl -L -o "$TMP_TGZ" "https://github.com/protomaps/go-pmtiles/releases/download/v1.30.1/go-pmtiles_1.30.1_Linux_x86_64.tar.gz"
  tar -xzf "$TMP_TGZ" -C "${WIKI_RUNTIME_ROOT}/bin" pmtiles
  rm -f "$TMP_TGZ"
  chmod +x "$PMTILES_BIN"
fi

if [[ "${OFFLINE_ONLY}" == "1" && "$SRC" =~ ^https?:// ]]; then
  echo "OFFLINE_ONLY=1 and source PMTiles is remote: $SRC" >&2
  exit 1
fi

echo "Dry-run estimate..."
"$PMTILES_BIN" extract "$SRC" "$OUT" --bbox="$BBOX" --maxzoom="$MAXZOOM" --dry-run

echo "Extracting PMTiles region..."
"$PMTILES_BIN" extract "$SRC" "$OUT" --bbox="$BBOX" --maxzoom="$MAXZOOM"

echo "Done: $OUT"
