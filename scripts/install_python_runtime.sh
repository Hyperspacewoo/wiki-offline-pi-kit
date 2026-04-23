#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=/dev/null
source "${SCRIPT_DIR}/layout.sh"

REQ_FILE="${1:-${WIKI_KIT_ROOT}/requirements/core.txt}"

if [[ ! -f "${REQ_FILE}" ]]; then
  echo "Requirements file not found: ${REQ_FILE}" >&2
  exit 1
fi

python3 -m venv "${WIKI_VENV}"
# shellcheck source=/dev/null
source "${WIKI_VENV}/bin/activate"

if [[ -d "${PYTHON_WHEELHOUSE}" ]] && find "${PYTHON_WHEELHOUSE}" -maxdepth 1 -type f -name '*.whl' | grep -q .; then
  echo "Installing Python dependencies from offline wheelhouse: ${PYTHON_WHEELHOUSE}"
  python -m pip install --no-index --find-links "${PYTHON_WHEELHOUSE}" -r "${REQ_FILE}"
else
  if [[ "${OFFLINE_ONLY}" == "1" ]]; then
    echo "OFFLINE_ONLY=1 and no wheels found in ${PYTHON_WHEELHOUSE}" >&2
    exit 1
  fi
  echo "Installing Python dependencies from PyPI"
  python -m pip install --upgrade pip
  python -m pip install -r "${REQ_FILE}"
fi
