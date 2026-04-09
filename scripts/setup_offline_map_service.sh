#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=/dev/null
source "${SCRIPT_DIR}/layout.sh"

write_layout_env_file "${WIKI_RUNTIME_ROOT}/layout.env"
sudo install -m 0644 "${WIKI_RUNTIME_ROOT}/layout.env" /etc/default/wiki-offline-kit

PYTHON_BIN="${WIKI_VENV}/bin/python"
if [[ ! -x "${PYTHON_BIN}" ]]; then
  PYTHON_BIN="$(command -v python3)"
fi

echo "Creating /etc/systemd/system/offline-map-ui.service"
sudo tee /etc/systemd/system/offline-map-ui.service > /dev/null <<EOF
[Unit]
Description=Offline OSM map web UI
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=${RUN_USER}
EnvironmentFile=/etc/default/wiki-offline-kit
WorkingDirectory=${WIKI_MAPS_DIR}
Environment=MAP_UI_PORT=8091
ExecStart=${PYTHON_BIN} ${WIKI_KIT_ROOT}/scripts/offline_map_ui.py
Restart=always
RestartSec=2

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable offline-map-ui.service
sudo systemctl restart offline-map-ui.service

systemctl status offline-map-ui.service --no-pager

echo "Done. Offline map UI: http://<PI_IP>:8091"
