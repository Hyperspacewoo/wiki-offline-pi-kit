PI WIKI KIT (Plug-and-Play)
===========================

Goal
----
Run offline knowledge on a Raspberry Pi (headless), with:
- Kiwix server (web search + article browsing)
- wikiask CLI (search + clean text extraction)
- auto-start on boot via systemd
- support for MULTIPLE ZIMs at once (Wikipedia + WikiMed + offline maps)
- simple web UI to choose active ZIMs
- one-click profiles in UI (General / Medical / Maps / All)

What to copy to Pi
------------------
1) This folder: wiki-offline-pi-kit
2) One or more ZIM files, e.g.:
   - wikipedia_en_all_nopic_2025-12.zim
   - wikem_en_all_maxi.zim (WikiMed)
   - openstreetmap_*.zim (offline maps)

Recommended location on Pi
--------------------------
- Put ZIMs on USB SSD mounted at: /mnt/wiki-ssd
- Example paths:
  /mnt/wiki-ssd/wikipedia_en_all_nopic_2025-12.zim
  /mnt/wiki-ssd/wikem_en_all_maxi.zim
  /mnt/wiki-ssd/openstreetmap_region.zim

Quick Start (on Pi)
-------------------
1) Copy this folder + ZIMs to Pi.

2) One-command setup (recommended):
   chmod +x run_all_on_pi.sh
   ./run_all_on_pi.sh \
     /mnt/wiki-ssd/wikipedia_en_all_nopic_2025-12.zim \
     /mnt/wiki-ssd/wikem_en_all_maxi.zim \
     /mnt/wiki-ssd/openstreetmap_region.zim

   Or auto-detect all ZIMs in a folder:
   chmod +x run_all_auto_zims.sh
   ./run_all_auto_zims.sh /mnt/wiki-ssd

3) Open in browser:
   - Kiwix reader: http://<PI_IP>:8080
   - ZIM selector UI: http://<PI_IP>:8090
   - In selector UI, use either:
     - individual checkboxes, or
     - one-click profiles (General / Medical / Maps / All)

4) Test:
   wiki-status
   zim-ui-status
   wiki-ask "black holes" --top 5 --open 1 --chars 2500

Manual (if needed)
------------------
chmod +x install_pi_wiki.sh setup_kiwix_service.sh setup_zim_ui_service.sh setup_sudoers_for_zim_ui.sh
./install_pi_wiki.sh
./setup_kiwix_service.sh /mnt/wiki-ssd/wikipedia_en_all_nopic_2025-12.zim /mnt/wiki-ssd/wikem_en_all_maxi.zim
./setup_zim_ui_service.sh
./setup_sudoers_for_zim_ui.sh

Useful commands
---------------
Start server now:
- wiki-start

Stop server:
- wiki-stop

Server status + logs:
- wiki-status

ZIM selector service status + logs:
- zim-ui-status

Ask/search from terminal:
- wiki-ask "quantum entanglement"

Where to get WikiMed + offline maps ZIMs
-----------------------------------------
- Main catalog: https://library.kiwix.org/
- Direct download index: https://download.kiwix.org/zim/

Look for:
- WikiMed (medical Wikipedia): usually under `wikipedia/` as `wikem_*` or similarly named medical ZIM builds
- OpenStreetMap/offline maps: under `other/` (search page for "openstreetmap")

Tip: pick `*_nopic` versions to save space if needed.

Troubleshooting
---------------
- Service logs:
  journalctl -u kiwix.service -n 100 --no-pager
  journalctl -u zim-selector.service -n 100 --no-pager
- If service doesn't start, confirm each ZIM path exists and is readable.
- If UI cannot restart kiwix: run `./setup_sudoers_for_zim_ui.sh` once.
- If kiwix fails with port error, check what owns 8080:
  `ss -ltnp | grep :8080`
  then stop old process or change port.
- For performance and durability, use USB SSD for ZIM storage.
