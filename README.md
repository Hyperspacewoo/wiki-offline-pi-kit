# Offgrid Intel Kit (Clean Structure)

Offline-first knowledge + maps bundle with Kiwix dashboard and local translation.

## Layout

- `scripts/` → installers, setup scripts, service helpers, Python apps
- `docs/` → user docs and project notes
- `config/` → bundle metadata/checksums
- `zims/` → bundled `.zim` files (canonical location)
- root launchers: `START_LINUX.sh`, `START_MAC.command`, `START_WINDOWS.bat`, `INSTALL_OFFLINE_KNOWLEDGE.sh`

## Quick Start (Linux)

```bash
./START_LINUX.sh
```

## Verify Bundle

```bash
./scripts/verify_checksums.sh
```

## Main URLs

- Dashboard: `http://<HOST_IP>:8090`
- Kiwix: `http://<HOST_IP>:8080`
- Offline map: `http://<HOST_IP>:8091`
