#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=/dev/null
source "${SCRIPT_DIR}/layout.sh"

echo "[1/6] Installing packages..."
sudo apt update
sudo apt install -y kiwix-tools python3-venv python3-pip jq build-essential cmake git

echo "[2/6] Creating runtime folders..."
ensure_wiki_layout

echo "[3/6] Creating Python venv..."
python3 -m venv "${WIKI_VENV}"
# shellcheck source=/dev/null
source "${WIKI_VENV}/bin/activate"
pip install --upgrade pip
pip install requests beautifulsoup4 lxml flask

echo "[4/6] Translator language setup (best effort)..."
"${WIKI_KIT_ROOT}/scripts/setup_translator.sh" || true

echo "[5/6] Installing executable permissions + env layout..."
chmod +x "${WIKI_KIT_ROOT}"/scripts/*.sh "${WIKI_KIT_ROOT}"/scripts/*.py || true
write_layout_env_file "${WIKI_RUNTIME_ROOT}/layout.env"
sudo install -m 0644 "${WIKI_RUNTIME_ROOT}/layout.env" /etc/default/wiki-offline-kit

echo "[6/6] Adding helper aliases to ~/.bashrc (if missing)..."
if ! grep -q "alias wiki-ask=" "$HOME/.bashrc"; then
  cat >> "$HOME/.bashrc" <<'EOF'
alias wiki-ask='source ~/wiki/.venv/bin/activate && python ${WIKI_KIT_ROOT:-$HOME/offline-knowledge/wiki-offline-pi-kit}/scripts/wikiask.py'
alias wiki-start='sudo systemctl start kiwix.service'
alias wiki-stop='sudo systemctl stop kiwix.service'
alias wiki-status='systemctl status kiwix.service --no-pager && echo && journalctl -u kiwix.service -n 20 --no-pager'
alias zim-ui-status='systemctl status zim-selector.service --no-pager && echo && journalctl -u zim-selector.service -n 20 --no-pager'
alias map-ui-status='systemctl status offline-map-ui.service --no-pager && echo && journalctl -u offline-map-ui.service -n 20 --no-pager'
alias llama-status='systemctl status llama-server.service --no-pager && echo && journalctl -u llama-server.service -n 20 --no-pager'
alias llama-start='sudo systemctl start llama-server.service'
alias llama-stop='sudo systemctl stop llama-server.service'
alias map-download='bash ${WIKI_KIT_ROOT:-$HOME/offline-knowledge/wiki-offline-pi-kit}/scripts/download_osm_pmtiles.sh'
alias map-places='bash ${WIKI_KIT_ROOT:-$HOME/offline-knowledge/wiki-offline-pi-kit}/scripts/setup_offline_place_index.sh'
EOF
fi

echo "Done. Runtime root: ${WIKI_RUNTIME_ROOT}"
echo "Bundle root:  ${WIKI_KIT_ROOT}"
echo "Open a new terminal or run: source ~/.bashrc"
