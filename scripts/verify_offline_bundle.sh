#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=/dev/null
source "${SCRIPT_DIR}/layout.sh"

pass=0
warns=0
fails=0

ok() { echo "[OK] $*"; pass=$((pass+1)); }
warn() { echo "[WARN] $*"; warns=$((warns+1)); }
fail() { echo "[MISSING] $*"; fails=$((fails+1)); }

any_match() {
  local dir="$1"
  local pattern="$2"
  [[ -d "$dir" ]] || return 1
  compgen -G "${dir}/${pattern}" > /dev/null
}

check_file() {
  local path="$1"
  local label="$2"
  if [[ -f "$path" ]]; then ok "$label"; else fail "$label -> $path"; fi
}

check_glob_required() {
  local dir="$1"
  local pattern="$2"
  local label="$3"
  if any_match "$dir" "$pattern"; then ok "$label"; else fail "$label -> ${dir}/${pattern}"; fi
}

check_glob_optional() {
  local dir="$1"
  local pattern="$2"
  local label="$3"
  if any_match "$dir" "$pattern"; then ok "$label"; else warn "$label -> ${dir}/${pattern}"; fi
}

echo "== Offline bundle verification =="
echo "Kit root: $WIKI_KIT_ROOT"
echo "Installers: $INSTALLERS_DIR"
echo

echo "-- Core bundle content --"
check_file "$WIKI_KIT_ROOT/INSTALL_OFFLINE_KNOWLEDGE.sh" "root installer present"
check_file "$WIKI_KIT_ROOT/scripts/install_prereqs_portable.sh" "portable prereq installer present"
check_file "$WIKI_KIT_ROOT/scripts/install_python_runtime.sh" "python runtime installer present"
check_file "$WIKI_KIT_ROOT/requirements/core.txt" "core requirements manifest present"
check_file "$WIKI_KIT_ROOT/requirements/translator.txt" "translator requirements manifest present"
check_file "$WIKI_KIT_ROOT/requirements/runtime.txt" "combined runtime requirements manifest present"

if [[ -f "$LLAMA_CPP_ROOT/CMakeLists.txt" ]]; then
  ok "llama.cpp source is vendored in repo"
else
  check_glob_required "$LLAMA_ARCHIVES_DIR" 'llama*.tar.gz' "offline llama.cpp source archive"
fi

check_glob_required "$AI_MODELS_DIR" '*.gguf' "bundled AI model(s)"
check_glob_required "$WIKI_KIT_ROOT/zims" '*.zim' "bundled ZIM content"

if [[ -x "$LLAMA_BIN" ]]; then
  file_out="$(file "$LLAMA_BIN" 2>/dev/null || true)"
  ok "prebuilt llama-server binary present"
  echo "      $file_out"
else
  warn "prebuilt llama-server binary not present (source build will be used)"
fi

echo

echo "-- Blank-machine offline add-ons needed for no-network install --"
check_glob_required "$INSTALLERS_DIR/apt" '*.deb' "Linux .deb prerequisite bundle"
check_glob_required "$PYTHON_WHEELHOUSE" 'flask*.whl' "core Python wheelhouse (flask)"
check_glob_required "$PYTHON_WHEELHOUSE" 'requests*.whl' "core Python wheelhouse (requests)"
check_file "$MAP_ASSETS_DIR/maplibre-gl.js" "bundled maplibre-gl.js"
check_file "$MAP_ASSETS_DIR/maplibre-gl.css" "bundled maplibre-gl.css"
check_file "$MAP_ASSETS_DIR/pmtiles.js" "bundled pmtiles.js"
check_file "$OFFLINE_DATASETS_DIR/US.zip" "bundled GeoNames US.zip"
check_file "$INSTALLER_BIN_DIR/pmtiles" "bundled pmtiles CLI"
check_glob_required "$MAP_BUNDLES_DIR" '*.pmtiles' "bundled offline map dataset(s)"
check_glob_optional "$PYTHON_WHEELHOUSE" 'argostranslate*.whl' "translator Python wheelhouse"
check_glob_optional "$ARGOS_MODELS_DIR" '*.argosmodel' "bundled Argos translator model(s)"

check_glob_optional "$INSTALLERS_DIR" 'python*.exe' "Windows Python bootstrap installer"
check_glob_optional "$INSTALLERS_DIR" 'wsl*.msi' "Windows WSL installer"
check_glob_optional "$INSTALLERS_DIR" 'Ubuntu*.*' "Windows Ubuntu WSL bundle"

echo

echo "-- Notes --"
if [[ -d "$INSTALLERS_DIR/apt" ]] && any_match "$INSTALLERS_DIR/apt" '*.deb'; then
  ok "local apt bundle detected; installer can try local package install first"
else
  warn "without installers/apt/*.deb, blank Ubuntu machines still need internet apt access"
fi
warn "offline translation is optional in the current installer flow, but requires translator wheels + .argosmodel files if you want it fully offline"
warn "Windows remains a bootstrap path into WSL; the bundled WSL/Ubuntu installers reduce setup friction, but first-run distro initialization may still require one launch on Windows"

if [[ "$fails" -gt 0 ]]; then
  echo
  echo "Summary: $pass ok, $warns warnings, $fails missing required offline artifact(s)."
  exit 1
fi

echo

echo "Summary: $pass ok, $warns warnings, $fails missing."
