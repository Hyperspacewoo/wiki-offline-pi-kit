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

sudo mkdir -p "${WIKI_MAPS_DIR}/static" "${WIKI_MAPS_DIR}/data"
sudo chown -R "${RUN_USER}:${RUN_USER}" "${WIKI_MAPS_DIR}"

# One-time migration from legacy root runtime if needed.
if [[ "${RUN_USER}" != "root" ]]; then
  if sudo test -d /root/wiki/maps; then
    if [[ -z "$(find "${WIKI_MAPS_DIR}/static" -maxdepth 1 -type f 2>/dev/null | head -n1 || true)" ]]; then
      sudo rsync -a /root/wiki/maps/static/ "${WIKI_MAPS_DIR}/static/" 2>/dev/null || true
    fi
    if [[ -z "$(find "${WIKI_MAPS_DIR}/data" -maxdepth 1 -type f 2>/dev/null | head -n1 || true)" ]]; then
      sudo rsync -a /root/wiki/maps/data/ "${WIKI_MAPS_DIR}/data/" 2>/dev/null || true
    fi
    sudo chown -R "${RUN_USER}:${RUN_USER}" "${WIKI_MAPS_DIR}" || true
  fi
fi

# Self-heal map prerequisites (best effort).
if [[ ! -f "${WIKI_MAPS_DIR}/static/maplibre-gl.js" || ! -f "${WIKI_MAPS_DIR}/static/maplibre-gl.css" || ! -f "${WIKI_MAPS_DIR}/static/pmtiles.js" ]]; then
  "${SCRIPT_DIR}/setup_offline_map_assets.sh" || true
fi
if [[ ! -f "${WIKI_MAPS_DIR}/data/us_places.tsv" ]]; then
  "${SCRIPT_DIR}/setup_offline_place_index.sh" || true
fi
if [[ -z "$(find "${WIKI_MAPS_DIR}/data" -maxdepth 1 -type f -name '*.pmtiles' 2>/dev/null | head -n1 || true)" ]]; then
  if [[ -d "${MAP_BUNDLES_DIR}" ]] && find "${MAP_BUNDLES_DIR}" -maxdepth 1 -type f -name '*.pmtiles' | grep -q .; then
    cp -f "${MAP_BUNDLES_DIR}"/*.pmtiles "${WIKI_MAPS_DIR}/data/"
  elif [[ "${OFFLINE_ONLY}" == "1" ]]; then
    echo "OFFLINE_ONLY=1 and no bundled .pmtiles files found in ${MAP_BUNDLES_DIR}" >&2
  else
    "${SCRIPT_DIR}/download_osm_pmtiles.sh" "-74.30,40.45,-73.65,40.95" "14" "${WIKI_MAPS_DIR}/data/nyc.pmtiles" || true
  fi
fi

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
