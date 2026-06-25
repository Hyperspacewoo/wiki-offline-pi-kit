# Manual Update Channel

Offgrid Kit uses manual update checks only. The dashboard never downloads or installs updates automatically.

## Customer Flow

1. Connect to the internet if available.
2. Open the dashboard.
3. Click **Updates**.
4. Click **Check Now**.
5. If an update is available, follow the release-notes/download link.

User content in these folders must be preserved by every update process:

- `models/`
- `ebooks/`
- `zims/`

## Operator Flow

The current kit reads its update source from `config/VERSION.json`:

```json
"update_manifest_url": "https://raw.githubusercontent.com/Hyperspacewoo/wiki-offline-pi-kit/main/config/update_manifest.json"
```

To announce a new version:

1. Publish the release artifact.
2. Add release notes.
3. Update `config/update_manifest.json` on GitHub.
4. Set `version` higher than the shipped `config/VERSION.json`.
5. Include a download URL and SHA-256 checksum when an updater package exists.

## Manifest Fields

- `version`: latest available version.
- `updated`: release date.
- `channel`: usually `stable`.
- `summary`: short customer-readable release note.
- `release_notes_url`: human-readable release notes.
- `download_url`: update package or release page.
- `checksum_sha256`: expected update package hash when a package is published.
- `preserve_user_content`: directories that must never be overwritten by updates.

## Release Rule

An update may replace application files, launchers, scripts, and bundled runtime assets. It must not delete or overwrite customer-added models, ebooks, or ZIM files.
