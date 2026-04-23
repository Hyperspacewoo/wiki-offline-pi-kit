#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=/dev/null
source "${SCRIPT_DIR}/layout.sh"

"${WIKI_KIT_ROOT}/scripts/install_python_runtime.sh" "${WIKI_KIT_ROOT}/requirements/translator.txt"
# shellcheck source=/dev/null
source "${WIKI_VENV}/bin/activate"

ARGOS_LANG_PAIRS="${ARGOS_LANG_PAIRS:-en:es,es:en}"
export ARGOS_MODELS_DIR OFFLINE_ONLY ARGOS_LANG_PAIRS

python - <<'PY'
import os
import traceback
from pathlib import Path
import argostranslate.package
import argostranslate.translate

pairs_raw = os.environ.get("ARGOS_LANG_PAIRS", "en:es,es:en")
offline_only = os.environ.get("OFFLINE_ONLY", "0") == "1"
argos_models_dir = Path(os.environ.get("ARGOS_MODELS_DIR", ""))
pairs = []
for p in [x.strip() for x in pairs_raw.split(",") if x.strip()]:
    if ":" in p:
        a, b = p.split(":", 1)
        pairs.append((a.strip(), b.strip()))

installed_pairs = []

try:
    if argos_models_dir.is_dir():
        for model in sorted(argos_models_dir.glob("*.argosmodel")):
            print(f"[INFO] Installing offline Argos model: {model.name}")
            argostranslate.package.install_from_path(str(model))
            installed_pairs.append(model.name)

    if not installed_pairs:
        if offline_only:
            raise RuntimeError(f"OFFLINE_ONLY=1 and no *.argosmodel files found in {argos_models_dir}")
        argostranslate.package.update_package_index()
        available = argostranslate.package.get_available_packages()
        for src, dst in pairs:
            pkg = next((x for x in available if x.from_code == src and x.to_code == dst), None)
            if not pkg:
                print(f"[WARN] No package found for {src}->{dst}")
                continue
            path = pkg.download()
            argostranslate.package.install_from_path(path)
            installed_pairs.append(f"{src}->{dst}")

    langs = [l.code for l in argostranslate.translate.get_installed_languages()]
    print("[OK] Installed translator language codes:", ", ".join(sorted(set(langs))))
    if installed_pairs:
        print("[OK] Installed language sources:", ", ".join(installed_pairs))
except Exception:
    print("[WARN] Translator language package setup failed (base libs installed).")
    traceback.print_exc()
PY

echo "Done. Translator setup complete (best effort)."
