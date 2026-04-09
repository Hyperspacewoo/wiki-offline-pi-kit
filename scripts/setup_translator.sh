#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=/dev/null
source "${SCRIPT_DIR}/layout.sh"

python3 -m venv "${WIKI_VENV}"
# shellcheck source=/dev/null
source "${WIKI_VENV}/bin/activate"

python -m pip install --upgrade pip
python -m pip install requests beautifulsoup4 lxml flask langdetect argostranslate

ARGOS_LANG_PAIRS="${ARGOS_LANG_PAIRS:-en:es,es:en}"

python - <<'PY'
import os
import traceback
import argostranslate.package
import argostranslate.translate

pairs_raw = os.environ.get("ARGOS_LANG_PAIRS", "en:es,es:en")
pairs = []
for p in [x.strip() for x in pairs_raw.split(",") if x.strip()]:
    if ":" in p:
        a, b = p.split(":", 1)
        pairs.append((a.strip(), b.strip()))

try:
    argostranslate.package.update_package_index()
    available = argostranslate.package.get_available_packages()
    done = []
    for src, dst in pairs:
        pkg = next((x for x in available if x.from_code == src and x.to_code == dst), None)
        if not pkg:
            print(f"[WARN] No package found for {src}->{dst}")
            continue
        path = pkg.download()
        argostranslate.package.install_from_path(path)
        done.append(f"{src}->{dst}")
    langs = [l.code for l in argostranslate.translate.get_installed_languages()]
    print("[OK] Installed translator language codes:", ", ".join(sorted(set(langs))))
    if done:
        print("[OK] Installed language pairs:", ", ".join(done))
except Exception:
    print("[WARN] Translator language package setup failed (base libs installed).")
    traceback.print_exc()
PY

echo "Done. Translator setup complete (best effort)."
