# National Launch Final Checklist

Use this checklist before selling or shipping a national batch.

## Must Pass

- Fresh Windows tester machine launches the dashboard.
- Fresh Linux tester machine launches the dashboard.
- Dashboard opens without internet.
- Knowledge/ZIM server opens.
- Map page opens.
- AI page responds or gives a clear local-service error.
- Translator page responds or gives a clear missing-pack message.
- `/field-cards` prints cleanly.
- `/offline-proof` shows installed counts.
- `/updates` returns a clear result with internet and a clear failure without internet.
- `scripts/verify_checksums.sh` passes on the final staged drive.

## Content And Legal

- Do not include quarantined ebooks.
- Include only ebooks with source/license sidecars.
- Keep `docs/OLD_EBOOK_REPOSITORY_REPLACEMENT_COMPARISON_2026-06-25.md`.
- Keep `docs/THIRD_PARTY_CONTENT_NOTICE.md`.
- Keep `docs/CONTENT_TAKEDOWN_POLICY.md`.
- Add a real support/takedown contact before broad paid release.

## Packaging

- Confirm product-facing name is **Offgrid Kit**.
- Include clear root launch files for Windows, macOS, and Linux.
- Include printed or printable quick-start instructions.
- Keep user content preservation policy: do not overwrite `models/`, `ebooks/`, or `zims/`.
- Run a USB speed test on sample shipped drives if AI startup feels slow.

## Update Channel

- Confirm `config/VERSION.json` has the correct current version.
- Confirm `config/update_manifest.json` exists on GitHub.
- Confirm `/updates` can fetch the manifest when online.
- For future releases, publish a checksum for downloadable update packages.

## Operator Sign-Off

Unsigned Windows launchers and unsigned checksum manifests can be acceptable for tester batches if documented. For broad retail distribution, code signing and signed release manifests reduce SmartScreen/support friction.
