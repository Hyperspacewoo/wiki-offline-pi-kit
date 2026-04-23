#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=/dev/null
source "${SCRIPT_DIR}/layout.sh"

echo "[1/6] Installing packages (if needed)..."
if command -v apt >/dev/null 2>&1; then
  sudo apt update
  sudo apt install -y kiwix-tools python3-venv python3-pip jq build-essential cmake git curl unzip rsync
else
  echo "apt not found; skipping package install (assume prereqs already provided)."
fi

echo "[2/6] Creating runtime folders..."
ensure_wiki_layout
if [[ "$(id -u)" -eq 0 && "${RUN_USER}" != "root" ]]; then
  chown -R "${RUN_USER}:${RUN_USER}" "${WIKI_RUNTIME_ROOT}"
fi

echo "[3/6] Creating Python venv + runtime dependencies..."
"${WIKI_KIT_ROOT}/scripts/install_python_runtime.sh"

echo "[4/6] Translator language setup (best effort)..."
"${WIKI_KIT_ROOT}/scripts/setup_translator.sh" || true

echo "[5/6] Installing executable permissions + env layout..."
chmod +x "${WIKI_KIT_ROOT}"/scripts/*.sh "${WIKI_KIT_ROOT}"/scripts/*.py || true
write_layout_env_file "${WIKI_RUNTIME_ROOT}/layout.env"
sudo install -m 0644 "${WIKI_RUNTIME_ROOT}/layout.env" /etc/default/wiki-offline-kit

BASHRC_PATH="${RUN_HOME}/.bashrc"
echo "[6/6] Adding helper aliases to ${BASHRC_PATH} (if missing)..."
touch "$BASHRC_PATH"
if ! grep -q "alias wiki-ask=" "$BASHRC_PATH"; then
  cat >> "$BASHRC_PATH" <<EOF
alias wiki-ask='source "${WIKI_VENV}/bin/activate" && python "${WIKI_KIT_ROOT}/scripts/wikiask.py"'
alias wiki-start='sudo systemctl start kiwix.service'
alias wiki-stop='sudo systemctl stop kiwix.service'
alias wiki-status='systemctl status kiwix.service --no-pager && echo && journalctl -u kiwix.service -n 20 --no-pager'
alias zim-ui-status='systemctl status zim-selector.service --no-pager && echo && journalctl -u zim-selector.service -n 20 --no-pager'
alias map-ui-status='systemctl status offline-map-ui.service --no-pager && echo && journalctl -u offline-map-ui.service -n 20 --no-pager'
alias llama-status='systemctl status llama-server.service --no-pager && echo && journalctl -u llama-server.service -n 20 --no-pager'
alias llama-start='sudo systemctl start llama-server.service'
alias llama-stop='sudo systemctl stop llama-server.service'
alias map-download='bash "${WIKI_KIT_ROOT}/scripts/download_osm_pmtiles.sh"'
alias map-places='bash "${WIKI_KIT_ROOT}/scripts/setup_offline_place_index.sh"'
EOF
fi
if [[ "$(id -u)" -eq 0 && "${RUN_USER}" != "root" ]]; then
  chown "${RUN_USER}:${RUN_USER}" "$BASHRC_PATH"
fi

echo "Done. Runtime root: ${WIKI_RUNTIME_ROOT}"
echo "Bundle root:  ${WIKI_KIT_ROOT}"
echo "Open a new terminal or run: source ${BASHRC_PATH}"
