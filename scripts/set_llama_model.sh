#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=/dev/null
source "${SCRIPT_DIR}/layout.sh"

MODEL_IN="${1:-}"
if [[ -z "${MODEL_IN}" ]]; then
  echo "Usage: $0 <model.gguf | absolute-model-path>" >&2
  exit 1
fi

if [[ "${MODEL_IN}" = /* ]]; then
  MODEL_PATH="${MODEL_IN}"
else
  MODEL_PATH="${AI_MODELS_DIR}/${MODEL_IN}"
fi

MODEL_PATH="$(readlink -f "${MODEL_PATH}")"
MODELS_DIR_REAL="$(readlink -f "${AI_MODELS_DIR}")"

if [[ ! -f "${MODEL_PATH}" ]]; then
  echo "Model file not found: ${MODEL_PATH}" >&2
  exit 1
fi

if [[ "${MODEL_PATH}" != "${MODELS_DIR_REAL}"/* ]]; then
  echo "Model must be inside ${MODELS_DIR_REAL}" >&2
  exit 1
fi

if [[ "${MODEL_PATH##*.}" != "gguf" ]]; then
  echo "Model must be a .gguf file" >&2
  exit 1
fi

export LLAMA_MODEL="${MODEL_PATH}"
export AI_MODEL_NAME="$(basename "${MODEL_PATH}")"

write_layout_env_file "${WIKI_RUNTIME_ROOT}/layout.env"
install -m 0644 "${WIKI_RUNTIME_ROOT}/layout.env" /etc/default/wiki-offline-kit
systemctl restart llama-server.service

echo "Selected model: ${LLAMA_MODEL}"
echo "Service restarted: llama-server.service"
