# QA Runbook (15–30 min)

## Pre-flight
```bash
cd ~/wiki-offline-pi-kit
chmod +x scripts/qa_smoke.sh
```

## 1) Automated smoke (2–5 min)
```bash
./scripts/qa_smoke.sh
```
Optional deeper read-only validation:
```bash
./scripts/qa_smoke.sh --admin-actions
```

## 2) Offline scenario checks (manual)
1. **No internet**: disable uplink and confirm dashboard/wiki/map still load.
2. **USB import**: plug test USB and import via UI or:
   ```bash
   ./scripts/import_zims_from_usb.sh /path/to/usb/zims
   ```
3. **Stale cache**: after import/rescan, refresh dashboard and verify latest ZIM list appears.
4. **Button smoke**: click all main + quick-action buttons.

## 3) Resilience checks
- **Reboot**: reboot host and rerun `./scripts/qa_smoke.sh`.
- **Power-loss** (release candidate only): unclean shutdown simulation, boot, rerun smoke.

## 4) Gate decision
Use docs:
- `docs/LAUNCH_CHECKLIST.md`
- `docs/OFFLINE_TEST_MATRIX.md`

Release only if all critical test cases pass.
