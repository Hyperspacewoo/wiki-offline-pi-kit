#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=/dev/null
source "${SCRIPT_DIR}/layout.sh"

# Preserve previously selected model when re-running setup
if [[ -f /etc/default/wiki-offline-kit ]]; then
  PREV_MODEL="$(grep '^LLAMA_MODEL=' /etc/default/wiki-offline-kit | head -n1 | cut -d= -f2- || true)"
  if [[ -n "${PREV_MODEL}" && -f "${PREV_MODEL}" ]]; then
    export LLAMA_MODEL="${PREV_MODEL}"
    export AI_MODEL_NAME="$(basename "${PREV_MODEL}")"
  fi
fi

write_layout_env_file "${WIKI_RUNTIME_ROOT}/layout.env"
sudo install -m 0644 "${WIKI_RUNTIME_ROOT}/layout.env" /etc/default/wiki-offline-kit

if [[ ! -x "${LLAMA_BIN}" ]]; then
  echo "ERROR: llama-server binary missing: ${LLAMA_BIN}" >&2
  echo "Build it first under: ${LLAMA_CPP_ROOT}" >&2
  exit 1
fi

if [[ ! -f "${LLAMA_MODEL}" ]]; then
  echo "ERROR: default model missing: ${LLAMA_MODEL}" >&2
  echo "Set LLAMA_MODEL in /etc/default/wiki-offline-kit or copy model into models/local-qwen." >&2
  exit 1
fi

echo "Creating /etc/systemd/system/llama-server.service"
sudo tee /etc/systemd/system/llama-server.service > /dev/null <<EOF
[Unit]
Description=llama.cpp local inference server
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=${RUN_USER}
EnvironmentFile=/etc/default/wiki-offline-kit
WorkingDirectory=${WIKI_KIT_ROOT}
ExecStart=${LLAMA_BIN} -m \${LLAMA_MODEL} --host \${LLAMA_HOST} --port \${LLAMA_PORT} -c \${LLAMA_CTX} -t \${LLAMA_THREADS}

Restart=always
RestartSec=2

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable llama-server.service
sudo systemctl restart llama-server.service

systemctl status llama-server.service --no-pager

echo "Done. llama.cpp UI/API: http://<HOST_IP>:${LLAMA_PORT}"
