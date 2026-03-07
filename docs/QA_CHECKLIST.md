# QA Checklist (Paid-Ready)

## Core UX
- [ ] Dashboard loads on `:8090`
- [ ] Four main actions visible: Knowledge / Maps / Translator / Ebooks
- [ ] First-run wizard opens at `/setup`

## Offline Features
- [ ] Wiki search works from local Kiwix
- [ ] Translator works for installed language packs
- [ ] Ebooks list page opens and serves files
- [ ] Map loads on `:8091` with no internet

## Reliability
- [ ] `scripts/doctor.sh` returns healthy status
- [ ] `scripts/verify_checksums.sh` passes
- [ ] Restart services and verify ports 8080/8090/8091

## Data / Distribution
- [ ] `zims/` populated
- [ ] `ebooks/` categories present
- [ ] External drive sync completed
- [ ] Release notes + version updated
