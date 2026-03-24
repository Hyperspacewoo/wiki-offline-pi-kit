#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=/dev/null
source "${SCRIPT_DIR}/layout.sh"

write_layout_env_file "${WIKI_RUNTIME_ROOT}/layout.env"
sudo install -m 0644 "${WIKI_RUNTIME_ROOT}/layout.env" /etc/default/wiki-offline-kit

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
ExecStart=${WIKI_VENV}/bin/python ${WIKI_KIT_ROOT}/scripts/zim_selector_ui.py
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
