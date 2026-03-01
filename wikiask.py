#!/usr/bin/env python3
import argparse
import requests
from bs4 import BeautifulSoup

BASE = "http://127.0.0.1:8080"

def search(query, limit=5):
    r = requests.get(f"{BASE}/search", params={"pattern": query}, timeout=30)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "lxml")

    results = []
    for a in soup.select("a[href]"):
        href = a.get("href", "")
        title = a.get_text(" ", strip=True)
        if "/content/" in href and title:
            if href.startswith("/"):
                href = BASE + href
            results.append((title, href))

    seen, uniq = set(), []
    for t, h in results:
        if h not in seen:
            seen.add(h)
            uniq.append((t, h))
    return uniq[:limit]

def fetch_text(url, max_chars=4000):
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    r.encoding = r.apparent_encoding or "utf-8"
    soup = BeautifulSoup(r.text, "lxml")

    for tag in soup(["script", "style", "nav", "header", "footer", "aside", "noscript"]):
        tag.decompose()

    main = (
        soup.select_one("#mw-content-text")
        or soup.select_one(".mw-parser-output")
        or soup.select_one("article")
        or soup.select_one("#content")
        or soup.body
        or soup
    )

    paras = [p.get_text(" ", strip=True) for p in main.select("p") if p.get_text(" ", strip=True)]
    text = "\n\n".join(paras) if paras else main.get_text("\n", strip=True)
    text = "\n".join(line for line in text.splitlines() if line.strip())
    return text[:max_chars]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("query", help="search query")
    ap.add_argument("--top", type=int, default=5)
    ap.add_argument("--open", type=int, default=1, help="which result to parse (1-based)")
    ap.add_argument("--chars", type=int, default=4000)
    args = ap.parse_args()

    hits = search(args.query, args.top)
    if not hits:
        print("No results found.")
        return

    print("\nTop results:")
    for i, (t, h) in enumerate(hits, 1):
        print(f"{i}. {t}\n   {h}")

    idx = max(1, min(args.open, len(hits))) - 1
    title, url = hits[idx]
    print(f"\n--- Parsed: {title} ---\n")
    print(fetch_text(url, args.chars))

if __name__ == "__main__":
    main()
