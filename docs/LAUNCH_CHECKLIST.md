# Launch Checklist (Release Readiness)

Use this checklist before shipping a production image/USB bundle.

## 1) Build + Artifact Integrity
- [ ] `git status` clean except intended release files
- [ ] `scripts/doctor.sh` reports all expected dirs/services/ports
- [ ] `scripts/verify_checksums.sh` passes
- [ ] `config/checksums.txt` includes all shipped ZIM + ebook assets
- [ ] Release tag/version recorded in release notes

## 2) Service Health
- [ ] `kiwix.service` active
- [ ] `zim-selector.service` active
- [ ] `offline-map-ui.service` active
- [ ] Ports listening: 8080, 8090, 8091
- [ ] Boot auto-start verified after reboot

## 3) Core UX (Button Smoke)
- [ ] Dashboard `http://<host>:8090` loads
- [ ] Setup page `http://<host>:8090/setup` loads
- [ ] Kiwix `http://<host>:8080` loads
- [ ] Map UI `http://<host>:8091` loads
- [ ] Buttons/shortcuts work: Knowledge, Maps, Translate, Library
- [ ] Quick actions work: Water, First Aid, Shelter, Emergency Phrase

## 4) Offline Resilience
- [ ] Works with WAN unplugged / Wi-Fi disabled
- [ ] Reboot recovery test passed (all services back)
- [ ] Power-loss recovery test passed (unclean shutdown)
- [ ] Stale-cache protection verified (dashboard no-cache headers)
- [ ] USB import path works and newly imported ZIM appears in UI

## 5) Release Packaging
- [ ] `scripts/export_bundle_to_usb.sh <usb-mount>` completed
- [ ] Random file open test from USB copy passed
- [ ] README + runbook included in exported bundle
- [ ] Final smoke: `scripts/qa_smoke.sh` (and `--admin-actions` if desired)

## Sign-off
- Release candidate: ___________________
- Operator: ____________________________
- Date/time: ___________________________
- Result: [ ] PASS  [ ] FAIL
- Notes: _______________________________________________
