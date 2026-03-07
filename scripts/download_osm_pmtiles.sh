#!/usr/bin/env bash
set -euo pipefail

# Defaults to NYC metro bbox and zoom suitable for laptop/Pi testing.
BBOX="${1:--74.30,40.45,-73.65,40.95}"
MAXZOOM="${2:-14}"
OUT="${3:-$HOME/wiki/maps/data/nyc.pmtiles}"
SRC="${4:-https://data.source.coop/protomaps/openstreetmap/v4.pmtiles}"

mkdir -p "$(dirname "$OUT")" "$HOME/wiki/bin"

PMTILES_BIN="$HOME/wiki/bin/pmtiles"
if [[ ! -x "$PMTILES_BIN" ]]; then
  echo "Downloading pmtiles CLI..."
  TMP_TGZ="$(mktemp)"
  curl -L -o "$TMP_TGZ" "https://github.com/protomaps/go-pmtiles/releases/download/v1.30.1/go-pmtiles_1.30.1_Linux_x86_64.tar.gz"
  tar -xzf "$TMP_TGZ" -C "$HOME/wiki/bin" pmtiles
  rm -f "$TMP_TGZ"
  chmod +x "$PMTILES_BIN"
fi

echo "Dry-run estimate..."
"$PMTILES_BIN" extract "$SRC" "$OUT" --bbox="$BBOX" --maxzoom="$MAXZOOM" --dry-run

echo "Extracting PMTiles region..."
"$PMTILES_BIN" extract "$SRC" "$OUT" --bbox="$BBOX" --maxzoom="$MAXZOOM"

echo "Done: $OUT"
