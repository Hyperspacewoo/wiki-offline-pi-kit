PI WIKI KIT (Polished Offline Knowledge + Maps)
===============================================

Overview
--------
This kit gives you a production-style offline stack on laptop or Pi:

Note on `pi-wiki-kit`: that older kit is optional now (legacy/simple terminal-first mode). The `wiki-offline-pi-kit` stack already includes terminal parsing/search (`wiki-ask`) plus the modern dashboard/map features.

- Kiwix server for ZIM libraries (`:8080`)
- Enterprise-style content manager dashboard (`:8090`)
- Offline OSM map UI with town search (`:8091`)
- CLI search helper (`wiki-ask`)
- Systemd services (auto-start on boot)

Core URLs
---------
- Kiwix Reader: `http://<HOST_IP>:8080`
- Content Manager Dashboard: `http://<HOST_IP>:8090`
- Offline Map UI: `http://<HOST_IP>:8091`

What’s New in the Dashboard (8090)
----------------------------------
- Automatically discovers **all ZIM files** from known roots:
  - `/mnt/wiki-ssd`
  - `~/wiki/zim`
  - `~/.openclaw/workspace/pi-wiki-kit`
  - `~/.openclaw/workspace/wiki-offline-pi-kit`
- Optional “extra folder” scan input to add one more source
- Fast client-side filter bar
- Select/unselect visible rows
- One-click profiles (All / General / Medical / Maps)
- Live stats (count, active, footprint, roots)

Quick Start
-----------
1) Put your ZIM files in one or more folders (recommended: `/mnt/wiki-ssd`).

2) Run setup:

```bash
cd ~/wiki-offline-pi-kit
chmod +x *.sh *.py
./run_all_auto_zims.sh /mnt/wiki-ssd
```

3) Open:
- `http://<HOST_IP>:8090` to manage ZIM selection
- `http://<HOST_IP>:8080` to browse content
- `http://<HOST_IP>:8091` for offline map + town search

Manual Setup (if needed)
------------------------
```bash
./install_pi_wiki.sh
./setup_kiwix_service.sh /mnt/wiki-ssd/wikipedia_en_all_nopic_2025-12.zim /mnt/wiki-ssd/wikem_en_all_maxi.zim
./setup_zim_ui_service.sh
./setup_sudoers_for_zim_ui.sh
./setup_offline_map_assets.sh
./setup_offline_map_service.sh
./download_osm_pmtiles.sh            # default NYC extract
./setup_offline_place_index.sh       # offline US town/city search index
```

Switch to USA map extract
-------------------------
```bash
~/wiki/bin/pmtiles extract https://data.source.coop/protomaps/openstreetmap/v4.pmtiles \
  ~/wiki/maps/data/usa.pmtiles --bbox=-125,24,-66,50 --maxzoom=10
```

Then update `~/wiki/maps/config.json`:
```json
{
  "title": "Offline OSM Map (USA Survival)",
  "pmtiles": "usa.pmtiles",
  "center": [-98.58, 39.83],
  "zoom": 4,
  "minZoom": 2,
  "maxZoom": 10
}
```

And restart map service:
```bash
sudo systemctl restart offline-map-ui.service
```

Useful Commands
---------------
- `wiki-status` – Kiwix status + logs
- `zim-ui-status` – Dashboard status + logs
- `map-ui-status` – Offline map service status + logs
- `wiki-ask "query"` – CLI article search/extract
- `map-download` – shortcut for `download_osm_pmtiles.sh`
- `map-places` – rebuild offline US place index

Where to Get ZIM Files
----------------------
- Library: https://library.kiwix.org/
- Direct index: https://download.kiwix.org/zim/

Suggested:
- Wikipedia (`wikipedia_*`)
- WikiMed (`wikem_*` / medical builds)
- Additional topical ZIMs as needed

Troubleshooting
---------------
- Kiwix logs:
  `journalctl -u kiwix.service -n 100 --no-pager`
- Dashboard logs:
  `journalctl -u zim-selector.service -n 100 --no-pager`
- Map logs:
  `journalctl -u offline-map-ui.service -n 100 --no-pager`
- If dashboard can’t restart Kiwix:
  run `./setup_sudoers_for_zim_ui.sh`
- If port conflict on 8080:
  `ss -ltnp | grep :8080`
