# Old Ebook Repository Replacement Comparison

Date: 2026-06-25

Scope: 133 unique old/quarantined ebook titles from `not-shipped-content/ebooks-review-required-2026-06-24`.

This is an operational release-screening result, not legal advice. A catalog hit from Open Library, Internet Archive, Google Books, Amazon, or another commercial source is not a redistribution license. The only automated replacement source treated as directly actionable for this pass was Project Gutenberg with `copyright=false`, subject to final human verification of the ebook license text and Project Gutenberg terms.

## Result

- `REPLACE_WITH_PROJECT_GUTENBERG`: 1
- `POSSIBLE_GUTENBERG_VERIFY`: 2
- `NO_REPLACEMENT_FOUND`: 130

## Replacement Candidates

| Old title | Replacement source | Status |
| --- | --- | --- |
| Camp life in the woods and the tricks of trapping and trap making containing comprehensive hunts | https://www.gutenberg.org/ebooks/17093 | Already restored to `ebooks/public-domain/` with sidecar |
| Deadfalls and snares a book on instruction for trappers about these | https://www.gutenberg.org/ebooks/34110 | Already restored to `ebooks/public-domain/` with sidecar |
| Shelters, Shacks and Shanties | https://www.gutenberg.org/ebooks/28255 | Already restored to `ebooks/public-domain/` with sidecar |

## Decision

No additional old ebooks should be restored from the quarantined folder for the paid product at this time.

The three Gutenberg-backed candidates are already included in the clean public-domain pack. The remaining old ebook titles are either modern commercial books, catalog-only references, borrow-only entries, generic/unclear filenames, or titles with no credible public-domain/permissive replacement found.

## Generated Evidence

Detailed local evidence files:

```text
C:\Users\Void\Desktop\wiki\not-shipped-content\ebooks-review-required-2026-06-24\OLD_EBOOK_REPOSITORY_REPLACEMENT_COMPARISON_2026-06-25.csv
C:\Users\Void\Desktop\wiki\not-shipped-content\ebooks-review-required-2026-06-24\OLD_EBOOK_REPOSITORY_REPLACEMENT_COMPARISON_2026-06-25.raw.jsonl
C:\Users\Void\Desktop\wiki\not-shipped-content\ebooks-review-required-2026-06-24\OLD_EBOOK_REPOSITORY_REPLACEMENT_COMPARISON_2026-06-25.md
```

Repeatable scan script:

```text
scripts/compare_old_ebooks_repositories.py
```
