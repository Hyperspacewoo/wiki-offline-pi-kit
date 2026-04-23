#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=/dev/null
source "${SCRIPT_DIR}/layout.sh"

DEB_DIR="${INSTALLERS_DIR}/apt"
mkdir -p "$DEB_DIR"

BASE_PACKAGES=(
  python3
  python3-venv
  python3-pip
  jq
  build-essential
  cmake
  git
  curl
  unzip
  rsync
  kiwix-tools
)

if [[ $# -gt 0 ]]; then
  BASE_PACKAGES+=("$@")
fi

resolve_packages() {
  apt-cache depends --recurse --important "${BASE_PACKAGES[@]}" \
    | awk '/^[A-Za-z0-9][^ :]*$/ {print $1} /^[[:space:]]+(PreDepends|Depends):/ {print $2}' \
    | sed -E 's/:amd64$//; /:i386$/d; /^<.*>$/d; /^$/d' \
    | sort -u
}

echo "== Refreshing apt metadata =="
sudo apt-get update

echo "== Resolving dependency-expanded package set =="
mapfile -t ALL_PACKAGES < <(resolve_packages)
printf '%s
' "${ALL_PACKAGES[@]}" > "$DEB_DIR/PACKAGES.txt"
echo "Expanded package set: ${#ALL_PACKAGES[@]} packages"

echo "== Downloading .deb files =="
for pkg in "${ALL_PACKAGES[@]}"; do
  if compgen -G "$DEB_DIR/${pkg}_*.deb" > /dev/null; then
    echo "Have ${pkg}"
    continue
  fi
  echo "Downloading ${pkg}"
  (
    cd "$DEB_DIR"
    apt download "$pkg"
  )
done

echo "Done. .deb bundle staged in $DEB_DIR"
