#!/usr/bin/env python3
"""Compare quarantined ebooks with public/commercial book repositories.

The output is an operational screening report, not legal advice. A catalog hit
from Open Library, Internet Archive, or Google Books is not a redistribution
license. Project Gutenberg `copyright=false` records are the safest automated
replacement candidates for the U.S. bundle, subject to Gutenberg terms and a
final human check of the ebook license text.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import time
from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path
from urllib.parse import quote

import requests


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_REVIEW_DIR = ROOT.parent.parent / "not-shipped-content" / "ebooks-review-required-2026-06-24"
USER_AGENT = "OffgridKitReleaseReview/1.0 (+local operator license screening)"


@dataclass
class OldEbook:
    title: str
    relative_path: str
    bytes: int


def clean_title_from_filename(path_text: str) -> str:
    stem = Path(path_text).stem
    stem = re.sub(r"[_-]+", " ", stem)
    stem = re.sub(r"\b(pdf|epub|mobi|azw3)\b", " ", stem, flags=re.I)
    stem = re.sub(r"\s+", " ", stem).strip()
    return stem


def norm(value: str) -> str:
    value = value.lower()
    value = value.replace("&", " and ")
    value = re.sub(r"[^a-z0-9]+", " ", value)
    value = re.sub(r"\b(the|a|an|and|or|of|to|in|for|with|by|on)\b", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def title_score(left: str, right: str) -> float:
    a = norm(left)
    b = norm(right)
    if not a or not b:
        return 0.0
    if a == b:
        return 1.0
    return SequenceMatcher(None, a, b).ratio()


def safe_get_json(session: requests.Session, url: str, timeout: int = 8) -> dict:
    for attempt in range(2):
        try:
            response = session.get(url, timeout=timeout)
            if response.status_code == 429:
                time.sleep(1.5 + attempt)
                continue
            response.raise_for_status()
            return response.json()
        except Exception as exc:
            if attempt == 1:
                return {"_error": str(exc)}
            time.sleep(0.5 + attempt)
    return {}


def load_old_ebooks(review_dir: Path) -> list[OldEbook]:
    strict_csv = review_dir / "INTERNET_LICENSE_REVIEW_EBOOKS_STRICT_PLUS.csv"
    moved_csv = review_dir / "MOVED_EBOOKS_REVIEW_REQUIRED.csv"
    records: dict[str, OldEbook] = {}

    if strict_csv.exists():
        with strict_csv.open(newline="", encoding="utf-8-sig") as handle:
            for row in csv.DictReader(handle):
                title = (row.get("title") or "").strip()
                rel = (row.get("relative_path") or "").strip()
                if not title:
                    title = clean_title_from_filename(rel)
                key = norm(title)
                if not key:
                    continue
                records[key] = OldEbook(title=title, relative_path=rel, bytes=int(row.get("bytes") or 0))

    if moved_csv.exists():
        with moved_csv.open(newline="", encoding="utf-8-sig") as handle:
            for row in csv.DictReader(handle):
                rel = (row.get("relative_path") or "").strip()
                title = clean_title_from_filename(rel)
                key = norm(title)
                if not key or key in records:
                    continue
                records[key] = OldEbook(title=title, relative_path=rel, bytes=int(row.get("bytes") or 0))

    return sorted(records.values(), key=lambda item: norm(item.title))


def search_gutendex(session: requests.Session, title: str) -> dict:
    url = f"https://gutendex.com/books/?languages=en&search={quote(title)}"
    data = safe_get_json(session, url)
    best = {}
    for item in (data.get("results") or [])[:10]:
        score = title_score(title, item.get("title") or "")
        if score > float(best.get("score") or 0):
            best = {
                "score": round(score, 3),
                "id": item.get("id"),
                "title": item.get("title") or "",
                "authors": "; ".join(a.get("name", "") for a in item.get("authors") or [] if a.get("name")),
                "copyright": item.get("copyright"),
                "url": f"https://www.gutenberg.org/ebooks/{item.get('id')}" if item.get("id") else "",
            }
    return best


def search_openlibrary(session: requests.Session, title: str) -> dict:
    url = f"https://openlibrary.org/search.json?title={quote(title)}&limit=5"
    data = safe_get_json(session, url)
    best = {}
    for item in data.get("docs") or []:
        score = title_score(title, item.get("title") or "")
        if score > float(best.get("score") or 0):
            key = item.get("key") or ""
            best = {
                "score": round(score, 3),
                "title": item.get("title") or "",
                "authors": "; ".join(item.get("author_name") or []),
                "first_publish_year": item.get("first_publish_year") or "",
                "public_scan": bool(item.get("public_scan_b")),
                "ebook_access": item.get("ebook_access") or "",
                "url": f"https://openlibrary.org{key}" if key else "",
            }
    return best


def search_google_books(session: requests.Session, title: str) -> dict:
    url = f"https://www.googleapis.com/books/v1/volumes?q=intitle:{quote(title)}&maxResults=5&printType=books"
    data = safe_get_json(session, url)
    best = {}
    for item in data.get("items") or []:
        info = item.get("volumeInfo") or {}
        score = title_score(title, info.get("title") or "")
        if score > float(best.get("score") or 0):
            sale = item.get("saleInfo") or {}
            access = item.get("accessInfo") or {}
            best = {
                "score": round(score, 3),
                "title": info.get("title") or "",
                "authors": "; ".join(info.get("authors") or []),
                "publisher": info.get("publisher") or "",
                "published_date": info.get("publishedDate") or "",
                "public_domain": bool(access.get("publicDomain")),
                "saleability": sale.get("saleability") or "",
                "url": info.get("infoLink") or "",
            }
    return best


def search_internet_archive(session: requests.Session, title: str) -> dict:
    query = f'title:("{title}") AND mediatype:(texts)'
    fields = "identifier,title,creator,date,licenseurl,rights,access-restricted-item"
    url = (
        "https://archive.org/advancedsearch.php"
        f"?q={quote(query)}&fl[]={fields.replace(',', '&fl[]=')}&rows=5&page=1&output=json"
    )
    data = safe_get_json(session, url)
    best = {}
    docs = ((data.get("response") or {}).get("docs") or [])
    for item in docs:
        score = title_score(title, item.get("title") or "")
        if score > float(best.get("score") or 0):
            licenseurl = item.get("licenseurl") or ""
            rights = item.get("rights") or ""
            restricted = str(item.get("access-restricted-item") or "").lower() == "true"
            shippable_hint = (not restricted) and bool(re.search(r"publicdomain|creativecommons\.org/(publicdomain|licenses/(by|by-sa|zero))", licenseurl, re.I))
            best = {
                "score": round(score, 3),
                "identifier": item.get("identifier") or "",
                "title": item.get("title") or "",
                "creator": item.get("creator") or "",
                "date": item.get("date") or "",
                "licenseurl": licenseurl,
                "rights": rights,
                "restricted": restricted,
                "shippable_hint": shippable_hint,
                "url": f"https://archive.org/details/{item.get('identifier')}" if item.get("identifier") else "",
            }
    return best


def classify(title: str, gutenberg: dict, archive: dict, openlibrary: dict, google: dict) -> tuple[str, str]:
    title_token_count = len(norm(title).split())
    if gutenberg and gutenberg.get("copyright") is False and float(gutenberg.get("score") or 0) >= 0.9:
        return "REPLACE_WITH_PROJECT_GUTENBERG", "Strong Project Gutenberg public-domain title match."
    if title_token_count >= 3 and gutenberg and gutenberg.get("copyright") is False and float(gutenberg.get("score") or 0) >= 0.72:
        return "POSSIBLE_GUTENBERG_VERIFY", "Possible public-domain Gutenberg match; verify title/author before replacing."
    if archive and archive.get("shippable_hint") and float(archive.get("score") or 0) >= 0.9:
        return "POSSIBLE_INTERNET_ARCHIVE_LICENSED_VERIFY", "Internet Archive has a strong match with public-domain/CC license metadata; verify item files and license."
    if google and google.get("public_domain") and float(google.get("score") or 0) >= 0.9:
        return "POSSIBLE_PUBLIC_DOMAIN_VERIFY", "Google Books marks a strong match public domain; find a clean source copy before shipping."
    if any(float(src.get("score") or 0) >= 0.82 for src in [archive, openlibrary, google] if src):
        return "CATALOG_OR_COMMERCIAL_ONLY", "Found catalog/commercial/borrowable metadata, but no redistribution-safe source."
    return "NO_REPLACEMENT_FOUND", "No credible public-domain or licensed replacement found in searched repositories."


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--review-dir", type=Path, default=DEFAULT_REVIEW_DIR)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--sources", choices=["all", "gutenberg"], default="all", help="Repository set to query. Gutenberg-only is fastest and produces the safest replacement candidates.")
    parser.add_argument("--include-google-books", action="store_true", help="Also query Google Books. Slower and used only as catalog/commercial evidence.")
    args = parser.parse_args()

    review_dir = args.review_dir.resolve()
    old = load_old_ebooks(review_dir)
    if args.limit:
        old = old[: args.limit]
    out_csv = review_dir / "OLD_EBOOK_REPOSITORY_REPLACEMENT_COMPARISON_2026-06-25.csv"
    out_jsonl = review_dir / "OLD_EBOOK_REPOSITORY_REPLACEMENT_COMPARISON_2026-06-25.raw.jsonl"
    out_md = review_dir / "OLD_EBOOK_REPOSITORY_REPLACEMENT_COMPARISON_2026-06-25.md"

    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})

    fieldnames = [
        "title",
        "relative_path",
        "bytes",
        "recommendation",
        "rationale",
        "gutenberg_score",
        "gutenberg_title",
        "gutenberg_authors",
        "gutenberg_copyright",
        "gutenberg_url",
        "internet_archive_score",
        "internet_archive_title",
        "internet_archive_licenseurl",
        "internet_archive_restricted",
        "internet_archive_url",
        "openlibrary_score",
        "openlibrary_title",
        "openlibrary_public_scan",
        "openlibrary_ebook_access",
        "openlibrary_url",
        "google_score",
        "google_title",
        "google_public_domain",
        "google_saleability",
        "google_url",
    ]

    rows = []
    with out_jsonl.open("w", encoding="utf-8", newline="\n") as raw_handle, out_csv.open("w", newline="", encoding="utf-8") as csv_handle:
        writer = csv.DictWriter(csv_handle, fieldnames=fieldnames)
        writer.writeheader()
        for idx, ebook in enumerate(old, 1):
            print(f"[{idx}/{len(old)}] {ebook.title}", flush=True)
            gutenberg = search_gutendex(session, ebook.title)
            openlibrary = search_openlibrary(session, ebook.title) if args.sources == "all" else {}
            archive = search_internet_archive(session, ebook.title) if args.sources == "all" else {}
            google = search_google_books(session, ebook.title) if args.include_google_books else {}
            recommendation, rationale = classify(ebook.title, gutenberg, archive, openlibrary, google)
            raw = {
                "ebook": ebook.__dict__,
                "gutenberg": gutenberg,
                "openlibrary": openlibrary,
                "internet_archive": archive,
                "google_books": google,
                "recommendation": recommendation,
                "rationale": rationale,
            }
            raw_handle.write(json.dumps(raw, ensure_ascii=True) + "\n")
            raw_handle.flush()
            row = {
                "title": ebook.title,
                "relative_path": ebook.relative_path,
                "bytes": ebook.bytes,
                "recommendation": recommendation,
                "rationale": rationale,
                "gutenberg_score": gutenberg.get("score", ""),
                "gutenberg_title": gutenberg.get("title", ""),
                "gutenberg_authors": gutenberg.get("authors", ""),
                "gutenberg_copyright": gutenberg.get("copyright", ""),
                "gutenberg_url": gutenberg.get("url", ""),
                "internet_archive_score": archive.get("score", ""),
                "internet_archive_title": archive.get("title", ""),
                "internet_archive_licenseurl": archive.get("licenseurl", ""),
                "internet_archive_restricted": archive.get("restricted", ""),
                "internet_archive_url": archive.get("url", ""),
                "openlibrary_score": openlibrary.get("score", ""),
                "openlibrary_title": openlibrary.get("title", ""),
                "openlibrary_public_scan": openlibrary.get("public_scan", ""),
                "openlibrary_ebook_access": openlibrary.get("ebook_access", ""),
                "openlibrary_url": openlibrary.get("url", ""),
                "google_score": google.get("score", ""),
                "google_title": google.get("title", ""),
                "google_public_domain": google.get("public_domain", ""),
                "google_saleability": google.get("saleability", ""),
                "google_url": google.get("url", ""),
            }
            writer.writerow(row)
            csv_handle.flush()
            rows.append(row)
            time.sleep(0.08)

    counts: dict[str, int] = {}
    for row in rows:
        counts[row["recommendation"]] = counts.get(row["recommendation"], 0) + 1
    priority = [r for r in rows if r["recommendation"].startswith("REPLACE") or r["recommendation"].startswith("POSSIBLE")]

    lines = [
        "# Old Ebook Repository Replacement Comparison",
        "",
        f"Date: 2026-06-25",
        f"Reviewed unique old ebook titles: {len(rows)}",
        "",
        "This is an automated repository comparison, not legal advice. Ship only files with a verified redistribution license sidecar.",
        "",
        "## Summary",
        "",
    ]
    for key in sorted(counts):
        lines.append(f"- {key}: {counts[key]}")
    lines.extend(["", "## Replacement Candidates", ""])
    if priority:
        lines.append("| Recommendation | Old title | Candidate | Source |")
        lines.append("| --- | --- | --- | --- |")
        for row in priority:
            candidate = row["gutenberg_title"] or row["internet_archive_title"] or row["google_title"]
            source = row["gutenberg_url"] or row["internet_archive_url"] or row["google_url"]
            lines.append(f"| {row['recommendation']} | {row['title']} | {candidate} | {source} |")
    else:
        lines.append("No automated public-domain/licensed replacement candidates found.")
    lines.extend([
        "",
        "## Files",
        "",
        f"- CSV: `{out_csv}`",
        f"- Raw JSONL: `{out_jsonl}`",
        "",
        "## Policy",
        "",
        "- Project Gutenberg: prefer `copyright=false` records, verify the license text inside the downloaded file, and keep a sidecar.",
        "- Internet Archive: treat catalog/borrowable hits as non-shippable unless the item has clear public-domain or compatible Creative Commons license metadata.",
        "- Open Library and Google Books: use as discovery/commercial catalog evidence only unless public-domain status leads to a clean source copy.",
    ])
    out_md.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    print(f"Wrote {out_csv}")
    print(f"Wrote {out_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
