#!/usr/bin/env bash
set -euo pipefail

echo "[1/5] Installing packages..."
sudo apt update
sudo apt install -y kiwix-tools python3-venv python3-pip jq

echo "[2/5] Creating folders..."
mkdir -p "$HOME/wiki/scripts" "$HOME/wiki/data" "$HOME/wiki/zim" "$HOME/wiki/maps/static" "$HOME/wiki/maps/data" "$HOME/wiki/bin"

echo "[3/5] Creating Python venv..."
python3 -m venv "$HOME/wiki/.venv"
source "$HOME/wiki/.venv/bin/activate"
pip install --upgrade pip
pip install requests beautifulsoup4 lxml flask

echo "[4/5] Installing scripts..."
cp ./wikiask.py "$HOME/wiki/scripts/wikiask.py"
cp ./zim_selector_ui.py "$HOME/wiki/scripts/zim_selector_ui.py"
cp ./kiwix-start-from-list.sh "$HOME/wiki/scripts/kiwix-start-from-list.sh"
cp ./setup_sudoers_for_zim_ui.sh "$HOME/wiki/scripts/setup_sudoers_for_zim_ui.sh"
cp ./offline_map_ui.py "$HOME/wiki/maps/offline_map_ui.py"
cp ./download_osm_pmtiles.sh "$HOME/wiki/scripts/download_osm_pmtiles.sh"
cp ./setup_offline_map_assets.sh "$HOME/wiki/scripts/setup_offline_map_assets.sh"
cp ./setup_offline_place_index.sh "$HOME/wiki/scripts/setup_offline_place_index.sh"
chmod +x "$HOME/wiki/scripts/wikiask.py" "$HOME/wiki/scripts/zim_selector_ui.py" "$HOME/wiki/scripts/kiwix-start-from-list.sh" "$HOME/wiki/scripts/setup_sudoers_for_zim_ui.sh" "$HOME/wiki/maps/offline_map_ui.py" "$HOME/wiki/scripts/download_osm_pmtiles.sh" "$HOME/wiki/scripts/setup_offline_map_assets.sh" "$HOME/wiki/scripts/setup_offline_place_index.sh"

echo "[5/5] Adding helper aliases to ~/.bashrc (if missing)..."
if ! grep -q "alias wiki-ask=" "$HOME/.bashrc"; then
  cat >> "$HOME/.bashrc" <<'EOF'
alias wiki-ask='source ~/wiki/.venv/bin/activate && python ~/wiki/scripts/wikiask.py'
alias wiki-start='sudo systemctl start kiwix.service'
alias wiki-stop='sudo systemctl stop kiwix.service'
alias wiki-status='systemctl status kiwix.service --no-pager && echo && journalctl -u kiwix.service -n 20 --no-pager'
alias zim-ui-status='systemctl status zim-selector.service --no-pager && echo && journalctl -u zim-selector.service -n 20 --no-pager'
alias map-ui-status='systemctl status offline-map-ui.service --no-pager && echo && journalctl -u offline-map-ui.service -n 20 --no-pager'
alias map-download='bash ~/wiki/scripts/download_osm_pmtiles.sh'
alias map-places='bash ~/wiki/scripts/setup_offline_place_index.sh'
EOF
fi

echo "Done. Open a new terminal or run: source ~/.bashrc"
