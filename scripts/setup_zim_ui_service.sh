#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Load installed environment first so reruns preserve deployed runtime/user paths.
if [[ -f /etc/default/wiki-offline-kit ]]; then
  set -a
  # shellcheck source=/dev/null
  source /etc/default/wiki-offline-kit
  set +a
fi

# shellcheck source=/dev/null
source "${SCRIPT_DIR}/layout.sh"

write_layout_env_file "${WIKI_RUNTIME_ROOT}/layout.env"
sudo install -m 0644 "${WIKI_RUNTIME_ROOT}/layout.env" /etc/default/wiki-offline-kit

PYTHON_BIN="${WIKI_VENV}/bin/python"
if [[ ! -x "${PYTHON_BIN}" ]]; then
  PYTHON_BIN="$(command -v python3)"
fi

echo "Creating /etc/systemd/system/zim-selector.service"
sudo tee /etc/systemd/system/zim-selector.service > /dev/null <<EOF
[Unit]
Description=Kiwix ZIM selector web UI
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=${RUN_USER}
EnvironmentFile=/etc/default/wiki-offline-kit
WorkingDirectory=${WIKI_KIT_ROOT}/scripts
ExecStart=${PYTHON_BIN} ${WIKI_KIT_ROOT}/scripts/zim_selector_ui.py
Restart=always
RestartSec=2

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable zim-selector.service
sudo systemctl restart zim-selector.service

systemctl status zim-selector.service --no-pager

echo "Done. ZIM selector UI: http://<PI_IP>:8090"
