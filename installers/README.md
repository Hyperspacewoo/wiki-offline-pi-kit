# Offline installer bundle layout

Use this folder when you want the kit to install on a **blank machine with little or no internet**.

## Required for fully offline Linux install

- `apt/*.deb`
  - Local Debian/Ubuntu packages for the Linux prerequisites used by the scripts and their dependency-expanded bundle
  - Seed with:
    - `./scripts/fetch_apt_bundle.sh`
  - Top-level packages covered:
    - `python3`
    - `python3-venv`
    - `python3-pip`
    - `jq`
    - `build-essential`
    - `cmake`
    - `git`
    - `curl`
    - `unzip`
    - `rsync`
    - `kiwix-tools`
- `python-wheels/*.whl`
  - Core wheelhouse for `requirements/core.txt`
- `map-assets/maplibre-gl.js`
- `map-assets/maplibre-gl.css`
- `map-assets/pmtiles.js`
- `datasets/US.zip`
  - GeoNames US dump for offline place search labels
- `bin/pmtiles`
  - Linux `pmtiles` CLI binary
- `maps/*.pmtiles`
  - At least one prebuilt offline map dataset for the map UI
## Optional for fully offline translation

- `python-wheels/*argostranslate*.whl` and related translator dependencies
  - Fetch with `./scripts/fetch_bundle_artifacts.sh --translator`
- `argos/*.argosmodel`
  - Translator language packs (for example `translate-en_es.argosmodel`, `translate-es_en.argosmodel`)

## Already bundled in this repo

These do **not** need separate installers right now:

- `llama.cpp/` source tree
- `models/local-qwen/*.gguf`
- bundled `zims/*.zim`

## Windows notes

Native Windows is still a bootstrap path into WSL.
For Windows convenience, add:

- `python*.exe`

You still need WSL + Ubuntu available on the target machine to run the Linux services.

## Seed most bundle artifacts automatically

If you are on a connected Linux machine, you can fetch most non-apt artifacts with:

```bash
./scripts/fetch_bundle_artifacts.sh [/path/to/local-map.pmtiles] [/path/to/translate-en_es.argosmodel]
./scripts/fetch_bundle_artifacts.sh --translator [/path/to/local-map.pmtiles] [/path/to/translate-en_es.argosmodel]
```

This fills:
- `python-wheels/`
- `map-assets/`
- `datasets/US.zip`
- `bin/pmtiles`
- any extra `.pmtiles` / `.argosmodel` paths you pass in
- translator wheels too, if you add `--translator`

It does **not** build a complete offline `.deb` mirror for you.

## Verify the bundle

Run:

```bash
./scripts/verify_offline_bundle.sh
```

To enforce strict offline expectations:

```bash
OFFLINE_ONLY=1 ./scripts/verify_offline_bundle.sh
```
