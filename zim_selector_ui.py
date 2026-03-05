#!/usr/bin/env python3
from flask import Flask, request, render_template_string, jsonify
from pathlib import Path
import subprocess
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote

app = Flask(__name__)

LIST_FILE = Path.home() / "wiki/data/active_zims.txt"
KIWIX_BASE = "http://127.0.0.1:8080"
DEFAULT_ROOTS = [
    Path("/mnt/wiki-ssd"),
    Path.home() / "wiki/zim",
    Path.home() / ".openclaw/workspace/pi-wiki-kit",
    Path.home() / ".openclaw/workspace/wiki-offline-pi-kit",
]

HTML = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Kiwix Unified Dashboard</title>
  <style>
    :root { --bg:#0b1020; --panel:#121a30; --panel2:#16223e; --text:#eaf0ff; --muted:#a9b5d1; --border:#2a3b63; }
    * { box-sizing: border-box; }
    body { margin:0; font-family: Inter, Segoe UI, Arial, sans-serif; background: radial-gradient(1200px 600px at 10% -20%, #243b70 0, transparent 60%), var(--bg); color:var(--text); }
    .wrap { max-width:1280px; margin:0 auto; padding:20px; }
    .hero, .card { border:1px solid var(--border); background:linear-gradient(180deg,var(--panel),var(--panel2)); border-radius:14px; padding:14px; margin-bottom:12px; }
    .hero h1 { margin:0 0 6px; font-size:24px; }
    .muted { color:var(--muted); font-size:13px; }
    .grid { display:grid; grid-template-columns:repeat(4,1fr); gap:10px; margin-top:10px; }
    .stat { border:1px solid var(--border); border-radius:10px; padding:10px; background:rgba(255,255,255,0.02); }
    .stat .k { color:var(--muted); font-size:12px; }
    .stat .v { font-size:20px; font-weight:700; }
    .row { display:flex; gap:8px; flex-wrap:wrap; align-items:center; }
    .grow { flex:1; }
    .btn { border:1px solid var(--border); border-radius:10px; padding:8px 12px; background:#1d2f57; color:#e7edff; cursor:pointer; text-decoration:none; display:inline-block; }
    .btn:hover { filter:brightness(1.08); }
    .btn.primary { background:linear-gradient(180deg,#4f8fff,#3b73d7); border-color:#6aa2ff; }
    .btn.mapcta { background: linear-gradient(180deg,#26d0a4,#138d6f); border-color:#50e1bd; font-weight:700; box-shadow:0 0 0 2px rgba(80,225,189,.18), 0 6px 20px rgba(19,141,111,.35); }
    input[type=text] { width:100%; padding:9px 11px; border:1px solid var(--border); border-radius:10px; background:#0f1830; color:var(--text); }
    .table { max-height:56vh; overflow:auto; border:1px solid var(--border); border-radius:10px; }
    table { width:100%; border-collapse:collapse; min-width:860px; }
    th, td { padding:9px; border-bottom:1px solid #24345d; text-align:left; font-size:14px; }
    th { position:sticky; top:0; background:#172549; }
    .badge { font-size:11px; border:1px solid var(--border); border-radius:999px; padding:2px 8px; }
    .split { display:grid; grid-template-columns:1fr 1fr; gap:10px; }
    @media (max-width: 1100px) { .grid{grid-template-columns:1fr 1fr;} .split{grid-template-columns:1fr;} }
  </style>
  <script>
    function quickFilter() {
      const q = (document.getElementById('q').value || '').toLowerCase();
      document.querySelectorAll('tbody tr[data-search]').forEach(tr => {
        tr.style.display = tr.dataset.search.includes(q) ? '' : 'none';
      });
    }
    async function rescan() {
      const extra = (document.getElementById('extraDir').value || '').trim();
      window.location = '/?scan_dir=' + encodeURIComponent(extra) + '&resync=1';
    }
    async function wikiSearch() {
      const q = (document.getElementById('wikiQ').value || '').trim();
      const list = document.getElementById('wikiResults');
      const parsed = document.getElementById('wikiParsed');
      parsed.textContent = '';
      if (!q) { list.innerHTML = '<div class="muted">Enter a search query.</div>'; return; }
      list.innerHTML = '<div class="muted">Searching…</div>';
      try {
        const rows = await fetch('/api/wiki/search?q=' + encodeURIComponent(q)).then(r => r.json());
        if (!rows.length) { list.innerHTML = '<div class="muted">No results.</div>'; return; }
        list.innerHTML = rows.map((r, i) => `
          <div style="padding:8px;border-bottom:1px solid #24345d;">
            <div><strong>${i+1}. ${r.title}</strong></div>
            <div class="muted"><a href="${r.url}" target="_blank">Open full article</a></div>
            <button class="btn" style="margin-top:6px;" onclick="wikiParse('${encodeURIComponent(r.url)}')">Parse excerpt</button>
          </div>
        `).join('');
      } catch (e) { list.innerHTML = '<div class="muted">Search failed.</div>'; }
    }
    async function wikiParse(encUrl) {
      const parsed = document.getElementById('wikiParsed');
      parsed.textContent = 'Parsing…';
      try {
        const data = await fetch('/api/wiki/parse?url=' + encUrl).then(r => r.json());
        parsed.textContent = data.text || 'No text extracted.';
      } catch (e) { parsed.textContent = 'Parse failed.'; }
    }
  </script>
</head>
<body>
  <div class="wrap">
    <div class="hero">
      <h1>Kiwix Unified Dashboard</h1>
      <p class="muted">All discovered ZIM files are always loaded. Click Open to launch that ZIM in a new browser tab.</p>
      <div class="grid">
        <div class="stat"><div class="k">Discovered ZIM files</div><div class="v">{{ total }}</div></div>
        <div class="stat"><div class="k">Loaded into Kiwix</div><div class="v">{{ loaded_count }}</div></div>
        <div class="stat"><div class="k">Storage footprint</div><div class="v">{{ total_size }}</div></div>
        <div class="stat"><div class="k">Roots scanned</div><div class="v">{{ roots_count }}</div></div>
      </div>
      {% if sync_msg %}<p class="muted" style="margin-top:8px;">{{ sync_msg }}</p>{% endif %}
    </div>

    <div class="card">
      <div class="row">
        <input id="extraDir" class="grow" type="text" placeholder="Optional extra folder to include" value="{{ scan_dir }}" />
        <button class="btn primary" onclick="rescan()">Rescan + Sync All ZIMs</button>
        <a class="btn mapcta" href="http://{{ host_ip }}:8091" target="_blank">🗺️ Open Offline Maps</a>
        <a class="btn" href="/help" target="_blank">Offline Help</a>
      </div>
      <p class="muted" style="margin-top:8px;">{{ roots|join(' • ') }}</p>
    </div>

    <div class="card">
      <div class="row" style="margin-bottom:8px;"><input id="q" class="grow" type="text" placeholder="Filter by title/category/path..." oninput="quickFilter()" /></div>
      <div class="table">
        <table>
          <thead><tr><th>Title</th><th>Category</th><th>Size</th><th>Action</th><th>Path</th></tr></thead>
          <tbody>
            {% for z in zims %}
            <tr data-search="{{ (z.title + ' ' + z.category + ' ' + z.path).lower() }}">
              <td>{{ z.icon }} <strong>{{ z.title }}</strong><div class="muted">{{ z.filename }}</div></td>
              <td><span class="badge">{{ z.category }}</span></td>
              <td>{{ z.size }}</td>
              <td><a class="btn" href="{{ z.open_url }}" target="_blank">Open</a></td>
              <td class="muted">{{ z.path }}</td>
            </tr>
            {% endfor %}
          </tbody>
        </table>
      </div>
    </div>

    <div class="card">
      <h3 style="margin:0 0 8px;">Wiki Search</h3>
      <div class="row"><input id="wikiQ" class="grow" type="text" placeholder="Search active content (e.g., black holes)" /><button class="btn primary" type="button" onclick="wikiSearch()">Search</button></div>
      <div class="split" style="margin-top:10px;">
        <div style="border:1px solid var(--border);border-radius:10px;max-height:240px;overflow:auto;padding:6px;" id="wikiResults"><div class="muted">Run a query to see results.</div></div>
        <div style="border:1px solid var(--border);border-radius:10px;max-height:240px;overflow:auto;padding:10px;white-space:pre-wrap;" id="wikiParsed"></div>
      </div>
    </div>
  </div>
</body>
</html>
"""

HELP_HTML = """
<!doctype html><html><head><meta charset='utf-8'><title>Offline Help</title><style>body{font-family:Inter,Arial,sans-serif;max-width:900px;margin:30px auto;padding:0 16px;color:#eaf0ff;background:#0b1020}h1,h2{color:#9ec0ff}code,pre{background:#13213f;padding:2px 6px;border-radius:6px}a{color:#7bb2ff}</style></head><body>
<h1>Offline Knowledge Kit – Help</h1>
<p>This system is designed to run without internet once installed.</p>
<h2>URLs</h2>
<ul><li>Dashboard: <code>:8090</code></li><li>Kiwix reader: <code>:8080</code></li><li>Offline maps: <code>:8091</code></li></ul>
<h2>USB Distribution</h2>
<ul><li>Run <code>START_LINUX.sh</code> (Linux), <code>START_WINDOWS.bat</code> (Windows), or <code>START_MAC.command</code> (macOS)</li><li>Use <code>verify_checksums.sh</code> before install</li></ul>
<h2>Troubleshooting</h2>
<ul><li>Check service status: <code>wiki-status</code>, <code>zim-ui-status</code>, <code>map-ui-status</code></li><li>Port check: <code>ss -ltnp | grep -E ':8080|:8090|:8091'</code></li></ul>
</body></html>
"""


def format_size(n: int) -> str:
    units = ["B", "KB", "MB", "GB", "TB"]
    x = float(n)
    for u in units:
        if x < 1024 or u == units[-1]:
            return f"{x:.1f} {u}" if u != "B" else f"{int(x)} B"
        x /= 1024
    return f"{n} B"


def build_roots(extra: str):
    roots = []
    for p in DEFAULT_ROOTS:
        if p.exists() and p.is_dir():
            roots.append(p)
    if extra:
        ep = Path(extra)
        if ep.exists() and ep.is_dir() and ep not in roots:
            roots.append(ep)
    out, seen = [], set()
    for r in roots:
        s = str(r.resolve())
        if s not in seen:
            seen.add(s)
            out.append(r)
    return out


def scan_zims(roots):
    files = {}
    for root in roots:
        for p in root.rglob("*.zim"):
            try:
                files[str(p.resolve())] = p
            except Exception:
                continue
    return sorted(files.values(), key=lambda p: str(p).lower())


def classify(name: str):
    n = name.lower()
    if "wikem" in n or "medicine" in n or "medical" in n:
        return "Medical", "🩺"
    if "openstreetmap" in n or "osm" in n or "map" in n:
        return "Maps", "🗺️"
    if "wikipedia" in n:
        return "Wikipedia", "📘"
    if "wikivoyage" in n:
        return "Travel", "🧭"
    if "wiktionary" in n:
        return "Dictionary", "📚"
    return "Other", "📦"


def pretty_title(name: str) -> str:
    stem = name[:-4] if name.lower().endswith(".zim") else name
    parts = [p for p in stem.replace("-", "_").split("_") if p]
    skip = {"all", "maxi", "nopic", "mini", "novid", "2024", "2025", "2026"}
    words = [p for p in parts if p.lower() not in skip and not p.isdigit()]
    words = words or parts
    return " ".join(w.capitalize() for w in words[:6])


def host_ip():
    try:
        out = subprocess.check_output(["hostname", "-I"], text=True).strip().split()
        return out[0] if out else "<PI_IP>"
    except Exception:
        return "<PI_IP>"


def restart_kiwix():
    subprocess.check_call(["sudo", "-n", "systemctl", "restart", "kiwix.service"])


def sync_all_loaded(paths):
    desired = [str(p) for p in paths]
    LIST_FILE.parent.mkdir(parents=True, exist_ok=True)
    current = []
    if LIST_FILE.exists():
        current = [line.strip() for line in LIST_FILE.read_text().splitlines() if line.strip() and not line.startswith("#")]
    if set(current) == set(desired):
        return "All discovered ZIM files are already loaded."
    LIST_FILE.write_text("\n".join(desired) + "\n")
    try:
        restart_kiwix()
        return f"Synced {len(desired)} ZIM files into Kiwix and restarted service."
    except Exception as e:
        return f"Synced list, but restart failed: {e}"


def wiki_search(query: str, limit: int = 8):
    r = requests.get(f"{KIWIX_BASE}/search", params={"pattern": query}, timeout=20)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "lxml")
    out, seen = [], set()
    for a in soup.select("a[href]"):
        href = a.get("href", "")
        title = a.get_text(" ", strip=True)
        if "/content/" not in href or not title:
            continue
        if href.startswith("/"):
            href = KIWIX_BASE + href
        if href in seen:
            continue
        seen.add(href)
        out.append({"title": title, "url": href})
        if len(out) >= limit:
            break
    return out


def wiki_parse(url: str, max_chars: int = 3500):
    r = requests.get(url, timeout=20)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "lxml")
    for tag in soup(["script", "style", "nav", "header", "footer", "aside", "noscript"]):
        tag.decompose()
    main = soup.select_one("#mw-content-text") or soup.select_one(".mw-parser-output") or soup.select_one("article") or soup.select_one("#content") or soup.body or soup
    paras = [p.get_text(" ", strip=True) for p in main.select("p") if p.get_text(" ", strip=True)]
    text = "\n\n".join(paras) if paras else main.get_text("\n", strip=True)
    text = "\n".join(line for line in text.splitlines() if line.strip())
    return text[:max_chars]


def build_page(extra_scan_dir: str, do_resync: bool):
    roots = build_roots(extra_scan_dir)
    paths = scan_zims(roots)
    sync_msg = sync_all_loaded(paths) if do_resync else ""

    zims, total_size = [], 0
    ip = host_ip()
    for p in paths:
        size_raw = p.stat().st_size if p.exists() else 0
        total_size += size_raw
        category, icon = classify(p.name)
        zims.append({
            "path": str(p),
            "filename": p.name,
            "zim_id": p.stem,
            "title": pretty_title(p.name),
            "icon": icon,
            "category": category,
            "size": format_size(size_raw),
            "open_url": f"http://{ip}:8080/content/{quote(p.stem)}/",
        })

    return render_template_string(
        HTML,
        zims=zims,
        total=len(zims),
        loaded_count=len(zims),
        total_size=format_size(total_size),
        roots=[str(r) for r in roots],
        roots_count=len(roots),
        scan_dir=extra_scan_dir,
        host_ip=ip,
        sync_msg=sync_msg,
    )


@app.get("/")
def index():
    scan_dir = request.args.get("scan_dir", "")
    do_resync = request.args.get("resync", "1") == "1"
    return build_page(scan_dir, do_resync)


@app.get("/help")
def help_page():
    return HELP_HTML


@app.get("/api/wiki/search")
def api_wiki_search():
    q = (request.args.get("q") or "").strip()
    if not q:
        return jsonify([])
    try:
        return jsonify(wiki_search(q))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.get("/api/wiki/parse")
def api_wiki_parse():
    url = (request.args.get("url") or "").strip()
    if not url:
        return jsonify({"text": ""})
    try:
        return jsonify({"text": wiki_parse(url)})
    except Exception as e:
        return jsonify({"error": str(e), "text": ""}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8090)
