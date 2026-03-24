#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 /absolute/path/to/wiki1.zim [/absolute/path/to/wiki2.zim ...]"
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=/dev/null
source "${SCRIPT_DIR}/layout.sh"

ZIMS=("$@")
for zim in "${ZIMS[@]}"; do
  if [[ ! -f "$zim" ]]; then
    echo "Error: file not found: $zim"
    exit 1
  fi
done

KIWIX_BIN="$(command -v kiwix-serve || true)"
if [[ -z "$KIWIX_BIN" ]]; then
  echo "Error: kiwix-serve not found. Run ./install_pi_wiki.sh first."
  exit 1
fi

ensure_wiki_layout
printf "%s\n" "${ZIMS[@]}" > "${ACTIVE_ZIMS_FILE}"
write_layout_env_file "${WIKI_RUNTIME_ROOT}/layout.env"
sudo install -m 0644 "${WIKI_RUNTIME_ROOT}/layout.env" /etc/default/wiki-offline-kit

echo "Creating /etc/systemd/system/kiwix.service"
sudo tee /etc/systemd/system/kiwix.service > /dev/null <<EOF
[Unit]
Description=Kiwix offline wiki server
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=${RUN_USER}
EnvironmentFile=/etc/default/wiki-offline-kit
WorkingDirectory=${WIKI_RUNTIME_ROOT}
ExecStart=${KIWIX_WRAPPER} ${ACTIVE_ZIMS_FILE} 8080
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

echo "Enabling and starting service..."
sudo systemctl daemon-reload
sudo systemctl enable kiwix.service
sudo systemctl restart kiwix.service

systemctl status kiwix.service --no-pager

echo "Serving ${#ZIMS[@]} ZIM file(s):"
for zim in "${ZIMS[@]}"; do
  echo " - $zim"
done

echo "Done. Access from LAN: http://<PI_IP>:8080"
