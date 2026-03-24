#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=/dev/null
source "${SCRIPT_DIR}/layout.sh"

ZIM_DIR="${1:-$WIKI_ZIM_DIR}"

if [[ ! -d "$ZIM_DIR" ]]; then
  echo "Error: directory not found: $ZIM_DIR"
  exit 1
fi

mapfile -d '' ZIMS < <(find "$ZIM_DIR" -maxdepth 2 -type f -iname '*.zim' -print0 | sort -z)

if [[ ${#ZIMS[@]} -eq 0 ]]; then
  echo "Error: no .zim files found in: $ZIM_DIR"
  exit 1
fi

echo "Found ${#ZIMS[@]} ZIM file(s):"
for z in "${ZIMS[@]}"; do
  echo " - $z"
done

cd "$SCRIPT_DIR"
chmod +x ./run_all_on_pi.sh
./run_all_on_pi.sh "${ZIMS[@]}"
