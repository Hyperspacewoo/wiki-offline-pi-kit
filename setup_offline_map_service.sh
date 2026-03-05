#!/usr/bin/env bash
set -euo pipefail

RUN_USER="$(id -un)"

echo "Creating /etc/systemd/system/offline-map-ui.service"
sudo tee /etc/systemd/system/offline-map-ui.service > /dev/null <<EOF
[Unit]
Description=Offline OSM map web UI
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=${RUN_USER}
WorkingDirectory=/home/${RUN_USER}/wiki/maps
Environment=MAP_UI_PORT=8091
ExecStart=/home/${RUN_USER}/wiki/.venv/bin/python /home/${RUN_USER}/wiki/maps/offline_map_ui.py
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
