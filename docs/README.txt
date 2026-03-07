OFFGRID INTEL KIT (USB-first Offline Archive)
=============================================

Purpose
-------
Run a complete offline archive stack from a portable kit and replicate it to other machines.

Main UI URLs
------------
- Unified Dashboard: `http://<HOST_IP>:8090`
- Kiwix Reader: `http://<HOST_IP>:8080`
- Offline Maps: `http://<HOST_IP>:8091`

Unified Flow
------------
- Dashboard always discovers and loads **all ZIM files** from known roots.
- Click **Open** on any row to launch that specific ZIM in a **new browser tab**.
- No separate “selection screen then reader screen” workflow.

Default discovery roots:
- `/mnt/wiki-ssd`
- `~/wiki/zim`
- `~/.openclaw/workspace/wiki-offline-pi-kit/zims`  (canonical local bundle folder)
- `~/.openclaw/workspace/wiki-offline-pi-kit`
- + optional extra directory entered in dashboard

Project structure note
----------------------
- Keep all bundled ZIM files in `zims/`.
- Top-level project directory is for scripts/services/docs only.

Wiki Search
-----------
Built into dashboard:
- search local Kiwix content
- parse clean excerpt in-place
- open full article in new tab

USB Distribution Files
----------------------
- `INSTALL_OFFLINE_KNOWLEDGE.sh` – one-command installer
- `START_LINUX.sh` – launcher for Linux
- `START_MAC.command` – launcher for macOS terminal flow
- `START_WINDOWS.bat` – Windows notice (use WSL Ubuntu)
- `config/VERSION.json` – release/version metadata
- `scripts/build_checksums.sh` / `scripts/verify_checksums.sh` – integrity workflow
- `scripts/import_zims_from_usb.sh` – copy ZIMs from removable media
- `scripts/export_bundle_to_usb.sh` – export this kit to another USB
- `scripts/check_ports_and_services.sh` – quick health check

Install (Linux)
---------------
```bash
chmod +x ./*.sh ./scripts/*.sh ./scripts/*.py
./INSTALL_OFFLINE_KNOWLEDGE.sh
```

Then open dashboard and click **Rescan + Sync All ZIMs**.

Create checksums before sharing
-------------------------------
```bash
./scripts/build_checksums.sh
./scripts/verify_checksums.sh
```

Maps
----
- Offline maps run at `:8091`.
- Dashboard has a prominent **Open Offline Maps** button.

CLI Query (simple)
------------------
```bash
source ~/wiki/.venv/bin/activate
wiki-ask "black holes"
wiki-ask "water purification" --top 5 --open 1 --chars 2500
```
