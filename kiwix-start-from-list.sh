#!/usr/bin/env bash
set -euo pipefail

LIST_FILE="${1:-$HOME/wiki/data/active_zims.txt}"
PORT="${2:-8080}"

if [[ ! -f "$LIST_FILE" ]]; then
  echo "Error: active ZIM list not found: $LIST_FILE"
  exit 1
fi

mapfile -t ZIMS < <(grep -v '^\s*#' "$LIST_FILE" | sed '/^\s*$/d')
if [[ ${#ZIMS[@]} -eq 0 ]]; then
  echo "Error: no ZIMs listed in $LIST_FILE"
  exit 1
fi

for zim in "${ZIMS[@]}"; do
  if [[ ! -f "$zim" ]]; then
    echo "Error: listed ZIM does not exist: $zim"
    exit 1
  fi
done

exec kiwix-serve --port="$PORT" "${ZIMS[@]}"
