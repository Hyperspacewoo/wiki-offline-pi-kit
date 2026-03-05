#!/usr/bin/env bash
set -euo pipefail

RUN_USER="$(id -un)"

echo "Creating /etc/systemd/system/zim-selector.service"
sudo tee /etc/systemd/system/zim-selector.service > /dev/null <<EOF
[Unit]
Description=Kiwix ZIM selector web UI
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=${RUN_USER}
WorkingDirectory=/home/${RUN_USER}/wiki/scripts
ExecStart=/home/${RUN_USER}/wiki/.venv/bin/python /home/${RUN_USER}/wiki/scripts/zim_selector_ui.py
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
