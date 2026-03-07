#!/usr/bin/env bash
set -euo pipefail

OUT="${1:-$HOME/wiki/maps/data/us_places.tsv}"
TMP_DIR="$(mktemp -d)"
ZIP_URL="https://download.geonames.org/export/dump/US.zip"

mkdir -p "$(dirname "$OUT")"

echo "Downloading US places dataset..."
curl -L -o "$TMP_DIR/US.zip" "$ZIP_URL"

unzip -q "$TMP_DIR/US.zip" -d "$TMP_DIR"

# geonames columns used:
# 2=name, 5=lat, 6=lon, 7=feature class, 8=feature code, 11=admin1, 15=population
# Keep populated places (P*) with population >= 1000 for responsive offline search/labels.
awk -F $'\t' 'BEGIN{OFS="\t"}
  $7=="P" && $15+0>=1000 {
    print $2, $11, $5, $6, $15
  }
' "$TMP_DIR/US.txt" > "$OUT"

rm -rf "$TMP_DIR"

echo "Wrote place index: $OUT"
wc -l "$OUT"
