#!/usr/bin/env bash
set -euo pipefail

# Canonical runtime + bundle layout for Offgrid Intel Kit.
# - WIKI_KIT_ROOT: immutable code/docs bundle (this repo copy)
# - WIKI_RUNTIME_ROOT: mutable runtime data, venv, maps config, active zims

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEFAULT_KIT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

# Use SUDO_USER if running via sudo to avoid root-home drift
if [[ -n "${SUDO_USER:-}" && "${RUN_USER:-}" == "root" ]]; then
  export RUN_USER="$SUDO_USER"
  export RUN_HOME=$(getent passwd "$SUDO_USER" | cut -d: -f6)
else
  export RUN_USER="${RUN_USER:-$(id -un)}"
  export RUN_HOME="${RUN_HOME:-$HOME}"
fi
export WIKI_KIT_ROOT="${WIKI_KIT_ROOT:-$DEFAULT_KIT_ROOT}"
export WIKI_RUNTIME_ROOT="${WIKI_RUNTIME_ROOT:-${RUN_HOME}/wiki}"

export WIKI_VENV="${WIKI_VENV:-${WIKI_RUNTIME_ROOT}/.venv}"
export WIKI_DATA_DIR="${WIKI_DATA_DIR:-${WIKI_RUNTIME_ROOT}/data}"
export WIKI_ZIM_DIR="${WIKI_ZIM_DIR:-${WIKI_RUNTIME_ROOT}/zim}"
export WIKI_EBOOK_DIR="${WIKI_EBOOK_DIR:-${WIKI_RUNTIME_ROOT}/ebooks}"
export WIKI_MAPS_DIR="${WIKI_MAPS_DIR:-${WIKI_RUNTIME_ROOT}/maps}"

export ACTIVE_ZIMS_FILE="${ACTIVE_ZIMS_FILE:-${WIKI_DATA_DIR}/active_zims.txt}"
export KIWIX_WRAPPER="${KIWIX_WRAPPER:-${WIKI_KIT_ROOT}/scripts/kiwix-start-from-list.sh}"

# Offline bundle artifact locations
export INSTALLERS_DIR="${INSTALLERS_DIR:-${WIKI_KIT_ROOT}/installers}"
export PYTHON_WHEELHOUSE="${PYTHON_WHEELHOUSE:-${INSTALLERS_DIR}/python-wheels}"
export ARGOS_MODELS_DIR="${ARGOS_MODELS_DIR:-${INSTALLERS_DIR}/argos}"
export MAP_ASSETS_DIR="${MAP_ASSETS_DIR:-${INSTALLERS_DIR}/map-assets}"
export OFFLINE_DATASETS_DIR="${OFFLINE_DATASETS_DIR:-${INSTALLERS_DIR}/datasets}"
export INSTALLER_BIN_DIR="${INSTALLER_BIN_DIR:-${INSTALLERS_DIR}/bin}"
export MAP_BUNDLES_DIR="${MAP_BUNDLES_DIR:-${INSTALLERS_DIR}/maps}"
export LLAMA_ARCHIVES_DIR="${LLAMA_ARCHIVES_DIR:-${INSTALLERS_DIR}}"
export OFFLINE_ONLY="${OFFLINE_ONLY:-0}"

# Local llama.cpp defaults (offline AI)
export LLAMA_CPP_ROOT="${LLAMA_CPP_ROOT:-${WIKI_KIT_ROOT}/llama.cpp}"
export LLAMA_BIN="${LLAMA_BIN:-${LLAMA_CPP_ROOT}/build/bin/llama-server}"
export LLAMA_HOST="${LLAMA_HOST:-0.0.0.0}"
export LLAMA_PORT="${LLAMA_PORT:-8092}"
export LLAMA_THREADS="${LLAMA_THREADS:-$(nproc)}"
export LLAMA_CTX="${LLAMA_CTX:-4096}"
export AI_MODELS_DIR="${AI_MODELS_DIR:-${WIKI_KIT_ROOT}/models/local-qwen}"
export LLAMA_MODEL_Q8="${LLAMA_MODEL_Q8:-${WIKI_KIT_ROOT}/models/local-qwen/Huihui-Qwen3.5-4B-abliterated.Q8_0.gguf}"
export LLAMA_MODEL_Q4="${LLAMA_MODEL_Q4:-${WIKI_KIT_ROOT}/models/local-qwen/Huihui-Qwen3.5-4B-abliterated.Q4_K_M.gguf}"
export LLAMA_MODEL="${LLAMA_MODEL:-${LLAMA_MODEL_Q8}}"
export AI_MODEL_NAME="${AI_MODEL_NAME:-$(basename "${LLAMA_MODEL}")}"
export AI_BASE="${AI_BASE:-http://127.0.0.1:${LLAMA_PORT}}"

ensure_wiki_layout() {
  mkdir -p "${WIKI_DATA_DIR}" "${WIKI_ZIM_DIR}" "${WIKI_EBOOK_DIR}" "${WIKI_MAPS_DIR}/static" "${WIKI_MAPS_DIR}/data"
}

write_layout_env_file() {
  local out="${1:-${WIKI_RUNTIME_ROOT}/layout.env}"
  mkdir -p "$(dirname "$out")"
  cat > "$out" <<EOF
RUN_USER=${RUN_USER}
RUN_HOME=${RUN_HOME}
WIKI_KIT_ROOT=${WIKI_KIT_ROOT}
WIKI_RUNTIME_ROOT=${WIKI_RUNTIME_ROOT}
WIKI_VENV=${WIKI_VENV}
WIKI_DATA_DIR=${WIKI_DATA_DIR}
WIKI_ZIM_DIR=${WIKI_ZIM_DIR}
WIKI_EBOOK_DIR=${WIKI_EBOOK_DIR}
WIKI_MAPS_DIR=${WIKI_MAPS_DIR}
ACTIVE_ZIMS_FILE=${ACTIVE_ZIMS_FILE}
KIWIX_WRAPPER=${KIWIX_WRAPPER}
LLAMA_CPP_ROOT=${LLAMA_CPP_ROOT}
LLAMA_BIN=${LLAMA_BIN}
LLAMA_HOST=${LLAMA_HOST}
LLAMA_PORT=${LLAMA_PORT}
LLAMA_THREADS=${LLAMA_THREADS}
LLAMA_CTX=${LLAMA_CTX}
AI_MODELS_DIR=${AI_MODELS_DIR}
LLAMA_MODEL_Q8=${LLAMA_MODEL_Q8}
LLAMA_MODEL_Q4=${LLAMA_MODEL_Q4}
LLAMA_MODEL=${LLAMA_MODEL}
AI_MODEL_NAME=${AI_MODEL_NAME}
AI_BASE=${AI_BASE}
INSTALLERS_DIR=${INSTALLERS_DIR}
PYTHON_WHEELHOUSE=${PYTHON_WHEELHOUSE}
ARGOS_MODELS_DIR=${ARGOS_MODELS_DIR}
MAP_ASSETS_DIR=${MAP_ASSETS_DIR}
OFFLINE_DATASETS_DIR=${OFFLINE_DATASETS_DIR}
INSTALLER_BIN_DIR=${INSTALLER_BIN_DIR}
MAP_BUNDLES_DIR=${MAP_BUNDLES_DIR}
LLAMA_ARCHIVES_DIR=${LLAMA_ARCHIVES_DIR}
OFFLINE_ONLY=${OFFLINE_ONLY}
EOF
}
