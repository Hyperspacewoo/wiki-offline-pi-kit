#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 /absolute/path/to/wikipedia.zim"
  echo "Example: $0 /mnt/wiki-ssd/wikipedia_en_all_nopic_2025-12.zim"
  exit 1
fi

ZIM_PATH="$1"
if [[ ! -f "$ZIM_PATH" ]]; then
  echo "Error: ZIM not found at: $ZIM_PATH"
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

chmod +x ./install_pi_wiki.sh ./setup_kiwix_service.sh ./wikiask.py

echo "==> Running installer..."
./install_pi_wiki.sh

echo "==> Creating/enabling kiwix systemd service..."
./setup_kiwix_service.sh "$ZIM_PATH"

echo "==> Final check"
source "$HOME/.bashrc" || true
wiki-status || true

echo "\nAll done."
echo "Use: wiki-ask \"quantum entanglement\" --top 5 --open 1 --chars 2500"
