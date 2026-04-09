#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 /absolute/path/to/wiki1.zim [/absolute/path/to/wiki2.zim ...]"
  echo "Example: $0 /mnt/wiki-ssd/wikipedia_en_all_nopic.zim /mnt/wiki-ssd/wikem_en_all_maxi.zim"
  exit 1
fi

ZIMS=("$@")
for zim in "${ZIMS[@]}"; do
  if [[ ! -f "$zim" ]]; then
    echo "Error: ZIM not found at: $zim"
    exit 1
  fi
done

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

chmod +x ./install_pi_wiki.sh ./setup_kiwix_service.sh ./setup_zim_ui_service.sh ./setup_sudoers_for_zim_ui.sh ./setup_offline_map_service.sh ./setup_offline_map_assets.sh ./setup_offline_place_index.sh ./download_osm_pmtiles.sh ./wikiask.py ./zim_selector_ui.py ./offline_map_ui.py ./kiwix-start-from-list.sh ./set_llama_model.sh ./setup_translator.sh ./setup_llama_cpp.sh
chmod +x ./start_llama_server.sh ./setup_llama_service.sh

echo "==> Running installer..."
./install_pi_wiki.sh

echo "==> Creating/enabling kiwix systemd service with ${#ZIMS[@]} ZIM(s)..."
./setup_kiwix_service.sh "${ZIMS[@]}"

echo "==> Creating/enabling ZIM selector UI service..."
./setup_zim_ui_service.sh

echo "==> Enabling passwordless restart/status for UI-triggered service actions..."
./setup_sudoers_for_zim_ui.sh

echo "==> Setting up offline map assets + service (port 8091)..."
./setup_offline_map_assets.sh
./setup_offline_map_service.sh

echo "==> Ensuring llama.cpp source + build..."
./setup_llama_cpp.sh

echo "==> Setting up llama.cpp AI service (port 8092)..."
./setup_llama_service.sh

echo "==> Downloading starter OSM extract (NYC bbox, maxzoom 14)..."
./download_osm_pmtiles.sh

echo "==> Building offline US place index for map labels/search..."
./setup_offline_place_index.sh

echo "==> Final check"
source "$HOME/.bashrc" || true
wiki-status || true
zim-ui-status || true
map-ui-status || true
llama-status || true

echo "\nAll done."
echo "Kiwix: http://<PI_IP>:8080"
echo "ZIM selector UI: http://<PI_IP>:8090"
echo "Offline map UI: http://<PI_IP>:8091"
echo "Offline AI UI/API: http://<PI_IP>:8092"
echo "Use: wiki-ask \"quantum entanglement\" --top 5 --open 1 --chars 2500"
