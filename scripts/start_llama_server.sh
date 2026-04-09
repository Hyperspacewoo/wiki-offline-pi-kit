#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=/dev/null
source "${SCRIPT_DIR}/layout.sh"

MODEL_CHOICE="${1:-q8}"
case "${MODEL_CHOICE}" in
  q4)
    MODEL_PATH="${LLAMA_MODEL_Q4}"
    ;;
  q8|*)
    MODEL_PATH="${LLAMA_MODEL_Q8}"
    ;;
esac

if [[ ! -x "${LLAMA_BIN}" ]]; then
  echo "llama-server binary not found or not executable: ${LLAMA_BIN}" >&2
  echo "Build first: cmake -S ${LLAMA_CPP_ROOT} -B ${LLAMA_CPP_ROOT}/build && cmake --build ${LLAMA_CPP_ROOT}/build -j" >&2
  exit 1
fi

if [[ ! -f "${MODEL_PATH}" ]]; then
  echo "Model not found: ${MODEL_PATH}" >&2
  exit 1
fi

echo "Starting llama-server"
echo "  model: ${MODEL_PATH}"
echo "  host : ${LLAMA_HOST}"
echo "  port : ${LLAMA_PORT}"

exec "${LLAMA_BIN}" \
  -m "${MODEL_PATH}" \
  --host "${LLAMA_HOST}" \
  --port "${LLAMA_PORT}" \
  -c "${LLAMA_CTX}" \
  -t "${LLAMA_THREADS}"
