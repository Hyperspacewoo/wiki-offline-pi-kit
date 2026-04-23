#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=/dev/null
source "${SCRIPT_DIR}/layout.sh"

PYTHON_VERSION="3.12.10"
PYTHON_URL="https://www.python.org/ftp/python/${PYTHON_VERSION}/python-${PYTHON_VERSION}-amd64.exe"
PYTHON_OUT="${INSTALLERS_DIR}/python-${PYTHON_VERSION}-amd64.exe"

WSL_VERSION="2.6.3.0"
WSL_URL="https://github.com/microsoft/WSL/releases/download/2.6.3/wsl.${WSL_VERSION}.x64.msi"
WSL_OUT="${INSTALLERS_DIR}/wsl.${WSL_VERSION}.x64.msi"

UBUNTU_BUNDLE_URL="https://aka.ms/wslubuntu2204"
UBUNTU_BUNDLE_OUT="${INSTALLERS_DIR}/Ubuntu2204-221101.AppxBundle"

mkdir -p "$INSTALLERS_DIR"

download_if_missing() {
  local url="$1"
  local out="$2"
  if [[ -s "$out" ]]; then
    echo "Have $(basename "$out")"
    return 0
  fi
  echo "Downloading $(basename "$out")"
  curl -L --fail --retry 3 --retry-delay 2 --continue-at - -o "$out" "$url"
}

download_if_missing "$PYTHON_URL" "$PYTHON_OUT"
download_if_missing "$WSL_URL" "$WSL_OUT"
download_if_missing "$UBUNTU_BUNDLE_URL" "$UBUNTU_BUNDLE_OUT"

echo
echo "Windows installer bundle ready in $INSTALLERS_DIR"
echo "Included:"
echo "- $(basename "$PYTHON_OUT")"
echo "- $(basename "$WSL_OUT")"
echo "- $(basename "$UBUNTU_BUNDLE_OUT")"
