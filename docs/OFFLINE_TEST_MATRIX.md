# Offline Test Matrix

Pass criteria are strict: any critical failure blocks release.

| ID | Scenario | Steps | Expected Result (PASS) | FAIL Criteria | Critical |
|---|---|---|---|---|---|
| OFF-01 | No internet operation | Disable WAN/Wi-Fi; load `:8090`, `:8080`, `:8091`; run a wiki search; open map and pan | All local apps load and are usable offline | Any app fails due to external dependency | Yes |
| OFF-02 | Reboot recovery | `sudo reboot`; after boot run `scripts/qa_smoke.sh` | Services auto-start and smoke passes | Service inactive, ports closed, or UI unreachable | Yes |
| OFF-03 | Power-loss recovery | Start workloads, hard power cycle (or pull power), reboot, run smoke + open latest content | Filesystem/service recovers, no corruption symptoms, app usable | Boot issues, data corruption, repeated service crash loop | Yes |
| OFF-04 | USB import | Attach known-good USB with `.zim`; run import action (UI or script); rescan | New ZIM is copied and appears in dashboard list/open link | Import fails, files missing, unreadable content | Yes |
| OFF-05 | Stale cache behavior | Load dashboard; inspect response headers; update content/rescan; hard refresh | `Cache-Control`/`Pragma` no-cache behavior; latest state shown | Old state persists after refresh due to stale cache | No |
| OFF-06 | Button smoke | Trigger `/go/*` actions for knowledge/maps/translate/library and quick actions | Redirects succeed and target pages open | Broken route, 4xx/5xx, dead button | Yes |

## Fast Execution Commands

```bash
# baseline smoke
./scripts/qa_smoke.sh

# include read-only admin checks (doctor + verify via API)
./scripts/qa_smoke.sh --admin-actions

# manual support checks
./scripts/doctor.sh
./scripts/verify_checksums.sh
```

## Test Evidence to Capture
- Date/time and tester name
- `qa_smoke.sh` output
- `systemctl status` snippets for all services
- Screenshot(s): dashboard, map page, successful imported ZIM
- Notes for any intermittent behavior
