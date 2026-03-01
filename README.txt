PI WIKI KIT (Plug-and-Play)
===========================

Goal
----
Run your offline Wikipedia ZIM on a Raspberry Pi (headless), with:
- Kiwix server (web search + article browsing)
- wikiask CLI (search + clean text extraction)
- auto-start on boot via systemd

What to copy to Pi
------------------
1) This folder: pi-wiki-kit
2) Your ZIM file (example): wikipedia_en_all_nopic_2025-12.zim

Recommended location on Pi
--------------------------
- Put ZIM on USB SSD mounted at: /mnt/wiki-ssd
- Final expected file path:
  /mnt/wiki-ssd/wikipedia_en_all_nopic_2025-12.zim

Quick Start (on Pi)
-------------------
1) Copy this folder + ZIM to Pi.

2) One-command setup (recommended):
   chmod +x run_all_on_pi.sh
   ./run_all_on_pi.sh /mnt/wiki-ssd/wikipedia_en_all_nopic_2025-12.zim

3) Test:
   wiki-status
   wiki-ask "black holes" --top 5 --open 1 --chars 2500

Manual (if needed)
------------------
chmod +x install_pi_wiki.sh setup_kiwix_service.sh
./install_pi_wiki.sh
./setup_kiwix_service.sh /mnt/wiki-ssd/wikipedia_en_all_nopic_2025-12.zim

Open browser from another device on LAN:
- http://<PI_IP>:8080

Useful commands
---------------
Start server now:
- wiki-start

Stop server:
- wiki-stop

Server status + logs:
- wiki-status

Ask/search from terminal:
- wiki-ask "quantum entanglement"

Troubleshooting
---------------
- Service logs:
  journalctl -u kiwix.service -n 100 --no-pager
- If service doesn't start, confirm the ZIM path exists and is readable.
- For performance and durability, use USB SSD for the ZIM.
