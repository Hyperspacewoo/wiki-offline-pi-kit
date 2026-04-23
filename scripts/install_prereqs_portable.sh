#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=/dev/null
source "${SCRIPT_DIR}/layout.sh"

mkdir -p "$INSTALLERS_DIR"

log() { echo "[prereqs] $*"; }
warn() { echo "[prereqs][warn] $*" >&2; }
have_cmd() { command -v "$1" >/dev/null 2>&1; }

APT_UPDATED=0
apt_update_once() {
  if [[ "$APT_UPDATED" == "0" ]]; then
    sudo apt-get update
    APT_UPDATED=1
  fi
}

install_local_deb_bundle_if_present() {
  local deb_dir="${INSTALLERS_DIR}/apt"
  if [[ -d "$deb_dir" ]] && find "$deb_dir" -maxdepth 1 -type f -name '*.deb' | grep -q .; then
    log "Installing local .deb bundle from ${deb_dir}"
    sudo apt-get install -y "$deb_dir"/*.deb
    return 0
  fi
  return 1
}

install_linux_repo_packages() {
  local desc="$1"
  shift
  if ! have_cmd apt-get; then
    warn "No supported package manager found for ${desc} (expected apt-get)."
    return 1
  fi
  if [[ "${OFFLINE_ONLY}" == "1" ]]; then
    warn "OFFLINE_ONLY=1 and no local .deb bundle was found for ${desc}."
    return 1
  fi
  log "Installing ${desc} via apt-get"
  apt_update_once
  sudo apt-get install -y "$@"
}

install_python_linux() {
  if have_cmd python3 && python3 -m venv --help >/dev/null 2>&1; then
    log "python3 already present"
    return 0
  fi
  install_linux_repo_packages "python3 runtime" python3 python3-venv python3-pip
}

install_build_tools_linux() {
  if have_cmd cmake && have_cmd make && have_cmd g++; then
    log "build tools already present"
    return 0
  fi
  install_linux_repo_packages "build tools" build-essential cmake git
}

install_support_tools_linux() {
  if have_cmd jq && have_cmd curl && have_cmd unzip && have_cmd rsync; then
    log "support tools already present"
    return 0
  fi
  install_linux_repo_packages "support tools" jq curl unzip rsync
}

install_kiwix_linux() {
  if have_cmd kiwix-serve; then
    log "kiwix-tools already present"
    return 0
  fi
  install_linux_repo_packages "kiwix-tools" kiwix-tools
}

install_python_windows() {
  if have_cmd python; then
    log "python already present on Windows"
    return 0
  fi
  local installer
  installer=$(find "$INSTALLERS_DIR" -maxdepth 1 -type f -iname 'python*.exe' | head -n1 || true)
  if [[ -z "$installer" ]]; then
    warn "Python installer not found in $INSTALLERS_DIR (expected python*.exe)"
    return 1
  fi
  log "Running Python installer: $(basename "$installer")"
  "$installer" /quiet InstallAllUsers=1 PrependPath=1 Include_test=0 || true
}

ensure_llama_cpp_repo_present() {
  if [[ -f "${LLAMA_CPP_ROOT}/CMakeLists.txt" ]]; then
    log "llama.cpp source present at ${LLAMA_CPP_ROOT}"
    return 0
  fi

  local tarball
  tarball=$(find "$LLAMA_ARCHIVES_DIR" -maxdepth 1 -type f \( -iname 'llama.cpp*.tar.gz' -o -iname 'llama.cpp*.tgz' -o -iname 'llama-cpp*.tar.gz' -o -iname 'llama-cpp*.tgz' \) | head -n1 || true)

  if [[ -n "$tarball" ]]; then
    log "Extracting offline llama.cpp bundle: $(basename "$tarball")"
    mkdir -p "$LLAMA_CPP_ROOT"
    tar -xzf "$tarball" -C "$LLAMA_CPP_ROOT" --strip-components=1
    return 0
  fi

  if [[ "${OFFLINE_ONLY}" == "1" ]]; then
    warn "OFFLINE_ONLY=1 and llama.cpp source archive is missing."
    return 1
  fi

  if have_cmd git; then
    log "No offline llama.cpp archive found; cloning from GitHub"
    git clone https://github.com/ggml-org/llama.cpp.git "$LLAMA_CPP_ROOT"
  else
    warn "Neither offline llama.cpp archive nor git is available"
    return 1
  fi
}

main() {
  case "$(uname -s)" in
    Linux)
      install_local_deb_bundle_if_present || true
      install_python_linux
      install_build_tools_linux
      install_support_tools_linux
      install_kiwix_linux
      ensure_llama_cpp_repo_present
      ;;
    MINGW*|MSYS*|CYGWIN*)
      install_python_windows
      ;;
    Darwin)
      warn "macOS auto-install is not fully automated in this script yet."
      ;;
    *)
      warn "Unsupported OS: $(uname -s)"
      ;;
  esac

  log "Prereq pass finished."
}

main "$@"
