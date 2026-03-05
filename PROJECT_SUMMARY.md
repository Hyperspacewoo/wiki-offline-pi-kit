# Offline Knowledge Server on Raspberry Pi (Headless)

This repo packages a lightweight, efficient offline knowledge stack:

- `kiwix-serve` for serving/searching `.zim` dumps
- `wikiask.py` for command-line search + clean paragraph extraction
- `systemd` service setup for auto-start at boot
- one-command installer (`run_all_on_pi.sh`)
- **multi-ZIM support** (Wikipedia + WikiMed + offline maps together)

## Why this design

No LLM is required for core search/parse. This keeps memory/CPU low and works on small hardware like a Raspberry Pi 4.

## Recommended hardware

- Minimum practical: Pi 4B 4GB + USB SSD
- Better: Pi 4B 8GB / Pi 5

## Quick usage

```bash
./run_all_on_pi.sh \
  /mnt/wiki-ssd/wikipedia_en_all_nopic_2025-12.zim \
  /mnt/wiki-ssd/wikem_en_all_maxi.zim \
  /mnt/wiki-ssd/openstreetmap_region.zim

wiki-ask "quantum entanglement" --top 5 --open 1 --chars 2500
```

## Note on ZIM files

ZIM files are intentionally **not committed** (very large). Transfer them separately to your Pi SSD.
