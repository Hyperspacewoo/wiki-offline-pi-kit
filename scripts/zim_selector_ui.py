#!/usr/bin/env python3
from flask import Flask, request, render_template_string, jsonify, send_file, abort, redirect
from pathlib import Path
import subprocess
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote, urlencode
import shlex
import os

app = Flask(__name__)


@app.after_request
def no_store(resp):
    resp.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    resp.headers["Pragma"] = "no-cache"
    resp.headers["Expires"] = "0"
    return resp

KIT_ROOT = Path(os.environ.get("WIKI_KIT_ROOT", Path(__file__).resolve().parent.parent))
RUNTIME_ROOT = Path(os.environ.get("WIKI_RUNTIME_ROOT", Path.home() / "wiki"))
LIST_FILE = Path(os.environ.get("ACTIVE_ZIMS_FILE", RUNTIME_ROOT / "data/active_zims.txt"))
KIWIX_BASE = os.environ.get("KIWIX_BASE", "http://127.0.0.1:8080")
DEFAULT_ROOTS = [
    Path("/mnt/wiki-ssd"),
    RUNTIME_ROOT / "zim",
    KIT_ROOT / "zims",
    KIT_ROOT,
]

EBOOK_ROOTS = [
    Path("/mnt/wiki-ssd/ebooks"),
    RUNTIME_ROOT / "ebooks",
    KIT_ROOT / "ebooks",
]
EBOOK_EXTS = {".pdf", ".epub", ".mobi", ".azw3", ".txt", ".md"}

HTML = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Offgrid Intel Kit • Luxury Offline Console</title>
  <style>
    :root {
      --bg:#0b1020;
      --panel:#121a2b;
      --panel2:#16223e;
      --text:#e6eaf2;
      --muted:#a9b5d1;
      --border:#2a3b63;
      --primary:#4f7cff;
      --accent:#2dd4bf;
      --warn:#f59e0b;
      --danger:#ef4444;
      --ok:#22c55e;
    }
    * { box-sizing: border-box; }
    body {
      margin:0;
      font-family: Inter, Segoe UI, Arial, sans-serif;
      background:
        radial-gradient(1200px 600px at 10% -20%, #243b70 0, transparent 60%),
        radial-gradient(900px 420px at 95% 0%, #183357 0, transparent 60%),
        var(--bg);
      color:var(--text);
    }
    .wrap { max-width:1240px; margin:0 auto; padding:24px; }
    .hero, .card {
      border:1px solid var(--border);
      background:linear-gradient(180deg,var(--panel),var(--panel2));
      border-radius:16px;
      padding:16px;
      margin-bottom:14px;
      box-shadow: 0 10px 30px rgba(2,8,23,.22);
    }
    .hero h1 { margin:0 0 6px; font-size:24px; }
    .muted { color:var(--muted); font-size:13px; }
    .row { display:flex; gap:8px; flex-wrap:wrap; align-items:center; }
    .grow { flex:1; }

    .grid { display:grid; grid-template-columns:repeat(4,1fr); gap:10px; margin-top:10px; }
    .stat { border:1px solid var(--border); border-radius:10px; padding:10px; background:rgba(255,255,255,0.02); }
    .stat .k { color:var(--muted); font-size:12px; }
    .stat .v { font-size:20px; font-weight:700; }

    .btn {
      border:1px solid var(--border);
      border-radius:12px;
      padding:9px 13px;
      background:#1d2f57;
      color:#e7edff;
      cursor:pointer;
      text-decoration:none;
      display:inline-block;
      transition: all .18s ease;
    }
    .btn:hover { filter:brightness(1.08); transform: translateY(-1px); }
    .btn.primary { background:linear-gradient(180deg,#4f8fff,#3b73d7); border-color:#6aa2ff; }
    .btn.mapcta {
      background: linear-gradient(180deg,#26d0a4,#138d6f);
      border-color:#50e1bd;
      font-weight:700;
      box-shadow:0 0 0 2px rgba(80,225,189,.18), 0 6px 20px rgba(19,141,111,.35);
    }

    input[type=text], select, textarea {
      width:100%;
      padding:9px 11px;
      border:1px solid var(--border);
      border-radius:10px;
      background:#0f1830;
      color:var(--text);
      font-family:inherit;
    }
    textarea { min-height:88px; resize:vertical; }

    .chips { display:flex; gap:6px; flex-wrap:wrap; margin:8px 0 0; }
    .chip {
      border:1px solid var(--border);
      border-radius:999px;
      padding:4px 10px;
      background:#122244;
      color:#dce7ff;
      cursor:pointer;
      font-size:12px;
    }
    .chip.active { background:#2c4f96; border-color:#6f9dff; }

    .table { max-height:56vh; overflow:auto; border:1px solid var(--border); border-radius:10px; }
    table { width:100%; border-collapse:collapse; min-width:860px; }
    th, td { padding:9px; border-bottom:1px solid #24345d; text-align:left; font-size:14px; }
    th { position:sticky; top:0; background:#172549; }
    .badge { font-size:11px; border:1px solid var(--border); border-radius:999px; padding:2px 8px; }

    .main-layout { display:grid; grid-template-columns:2fr 1fr; gap:12px; }
    .split { display:grid; grid-template-columns:1fr 1fr; gap:10px; }

    .translator-grid { display:grid; grid-template-columns:1fr 1fr; gap:10px; }
    .status-dot {
      width:8px; height:8px; border-radius:999px; display:inline-block; margin-right:6px;
      background:var(--ok);
      box-shadow:0 0 0 5px rgba(34,197,94,.15);
    }
    .status-dot.warn { background:var(--warn); box-shadow:0 0 0 5px rgba(245,158,11,.15); }
    .pill {
      font-size:11px;
      border:1px solid #2f4b80;
      background:#0f1c3c;
      color:#b8ccf8;
      border-radius:999px;
      padding:3px 8px;
    }

    pre {
      margin:0;
      white-space:pre-wrap;
      border:1px solid var(--border);
      border-radius:10px;
      padding:10px;
      background:#0f1830;
      color:#dbe7ff;
      font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
      font-size:12px;
      line-height:1.45;
    }

    @media (max-width: 1100px) {
      .grid{grid-template-columns:1fr 1fr;}
      .split{grid-template-columns:1fr;}
      .main-layout{grid-template-columns:1fr;}
      .translator-grid{grid-template-columns:1fr;}
    }
  </style>
  <script>
    let activeCategory = 'all';

    function applyFilters() {
      const q = (document.getElementById('q').value || '').toLowerCase();
      let visible = 0;
      document.querySelectorAll('tbody tr[data-search]').forEach(tr => {
        const matchText = tr.dataset.search.includes(q);
        const matchCategory = activeCategory === 'all' || tr.dataset.category === activeCategory;
        const show = matchText && matchCategory;
        tr.style.display = show ? '' : 'none';
        if (show) visible += 1;
      });
      const c = document.getElementById('visibleCount');
      if (c) c.textContent = visible;
    }

    function quickFilter() { applyFilters(); }

    function setCategory(cat, el) {
      activeCategory = cat;
      document.querySelectorAll('.chip').forEach(x => x.classList.remove('active'));
      if (el) el.classList.add('active');
      applyFilters();
    }

    function sortRows() {
      const mode = (document.getElementById('sortMode').value || 'title_asc');
      const tbody = document.querySelector('tbody');
      const rows = Array.from(tbody.querySelectorAll('tr[data-search]'));
      rows.sort((a, b) => {
        const ta = a.dataset.title || '';
        const tb = b.dataset.title || '';
        const sa = parseInt(a.dataset.sizeBytes || '0', 10);
        const sb = parseInt(b.dataset.sizeBytes || '0', 10);
        if (mode === 'title_desc') return tb.localeCompare(ta);
        if (mode === 'size_desc') return sb - sa;
        if (mode === 'size_asc') return sa - sb;
        return ta.localeCompare(tb);
      });
      rows.forEach(r => tbody.appendChild(r));
      applyFilters();
    }

    function clearFilters() {
      document.getElementById('q').value = '';
      activeCategory = 'all';
      document.querySelectorAll('.chip').forEach(x => x.classList.remove('active'));
      const all = document.querySelector('.chip[data-cat="all"]');
      if (all) all.classList.add('active');
      applyFilters();
    }

    async function rescan() {
      const extra = (document.getElementById('extraDir').value || '').trim();
      window.location = '/?scan_dir=' + encodeURIComponent(extra) + '&resync=1';
    }

    async function runAdminAction(action) {
      const out = document.getElementById('adminOut');
      if (out) out.textContent = 'Running ' + action + '...';
      try {
        const r = await fetch('/api/admin/action', {
          method: 'POST',
          headers: {'Content-Type':'application/json'},
          body: JSON.stringify({action})
        });
        const data = await r.json();
        if (out) out.textContent = (data.ok ? '✅ ' : '⚠️ ') + (data.message || '') + (data.output ? '\n\n' + data.output : '');
      } catch (e) {
        if (out) out.textContent = 'Failed: ' + e;
      }
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

    async function wikiParse(url) {
      const parsed = document.getElementById('wikiParsed');
      parsed.textContent = 'Parsing…';
      try {
        const data = await fetch('/api/wiki/parse?url=' + encodeURIComponent(url)).then(r => r.json());
        parsed.textContent = data.text || 'No text extracted.';
      } catch (e) { parsed.textContent = 'Parse failed.'; }
    }

    function quickAction(kind) {
      const status = document.getElementById('quickActionStatus');
      if (kind === 'translate') {
        document.getElementById('trInput').value = 'I need medical help';
        document.getElementById('trSource').value = 'en';
        document.getElementById('trTarget').value = 'es';
        const t = document.getElementById('translator');
        if (t) t.scrollIntoView({behavior:'smooth', block:'start'});
        if (status) status.textContent = 'Prepared emergency translation phrase.';
        return;
      }
      const queries = {
        water: 'water purification',
        firstaid: 'first aid',
        shelter: 'shelter building'
      };
      const q = queries[kind] || '';
      if (!q) return;
      const input = document.getElementById('wikiQ');
      input.value = q;
      const section = document.getElementById('wiki-search');
      if (section) section.scrollIntoView({behavior:'smooth', block:'start'});
      wikiSearch();
      if (status) status.textContent = `Searching for: ${q}`;
    }

    function swapTranslatorLangs() {
      const src = document.getElementById('trSource');
      const dst = document.getElementById('trTarget');
      const t = src.value;
      src.value = dst.value;
      dst.value = t;
    }

    async function translateText() {
      const input = (document.getElementById('trInput').value || '').trim();
      const source = document.getElementById('trSource').value;
      const target = document.getElementById('trTarget').value;
      const output = document.getElementById('trOutput');
      const meta = document.getElementById('trMeta');
      if (!input) { output.value = ''; meta.textContent = 'Enter text to translate.'; return; }
      output.value = 'Translating…';
      meta.textContent = '';
      try {
        const res = await fetch('/api/translate', {
          method: 'POST',
          headers: {'Content-Type':'application/json'},
          body: JSON.stringify({text: input, source, target})
        });
        const data = await res.json();
        if (!res.ok || data.error) {
          output.value = '';
          meta.textContent = data.error || 'Translation failed.';
          return;
        }
        output.value = data.translation || '';
        const conf = data.confidence ? ` • confidence: ${Math.round(data.confidence * 100)}%` : '';
        meta.textContent = `engine: ${data.engine || 'offline'} • detected: ${data.detected || source}${conf}`;
      } catch (e) {
        output.value = '';
        meta.textContent = 'Translation failed.';
      }
    }

    document.addEventListener('DOMContentLoaded', () => {
      applyFilters();
      const filterInput = document.getElementById('q');
      document.addEventListener('keydown', (e) => {
        if (e.key === '/' && document.activeElement !== filterInput) {
          e.preventDefault();
          filterInput.focus();
        }
      });
    });
  </script>
</head>
<body>
  <div class="wrap">
    <div class="hero">
      <div class="row" style="justify-content:space-between;align-items:flex-start;">
        <div>
          <h1>Offgrid Intel Kit</h1>
          <p class="muted">Luxury offline intelligence console — instant access to knowledge, maps, translation, and field-ready reading.</p>
        </div>
        <div class="pill"><span class="status-dot {{ 'warn' if translator_offline_warning else '' }}"></span>{{ translator_status }}</div>
      </div>
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
        <a class="btn primary" href="http://{{ host_ip }}:8080" target="_blank" style="font-weight:700;">📘 Knowledge</a>
        <a class="btn mapcta" href="http://{{ host_ip }}:8091">🗺️ Maps</a>
        <a class="btn" href="#translator">🈯 Translate</a>
        <a class="btn" href="/ebooks">📚 Library</a>
      </div>
      <div class="row" style="margin-top:8px;">
        <a class="btn" href="/morse">📡 Morse</a>
        <a class="btn" href="/help">Support</a>
      </div>
      <div class="row" style="margin-top:8px;">
        <input id="extraDir" class="grow" type="text" placeholder="Optional extra folder to include" value="{{ scan_dir }}" />
        <button class="btn primary" onclick="rescan()">Rescan + Sync All ZIMs</button>
      </div>
      <p class="muted" style="margin-top:8px;">{{ roots|join(' • ') }}</p>
    </div>

    <div class="card">
      <div class="row">
        <a class="btn" href="/go/water" target="_blank">💧 Water Purification</a>
        <a class="btn" href="/go/firstaid" target="_blank">🩹 First Aid</a>
        <a class="btn" href="/go/shelter" target="_blank">🏕️ Shelter</a>
        <a class="btn" href="/?qa=translate#translator">🈺 Emergency Phrase</a>
      </div>
      <p id="quickActionStatus" class="muted" style="margin-top:8px;">{{ qa_status or 'Tap any action to jump instantly.' }}</p>
    </div>

    <div class="main-layout">
      <div>
        <div class="card" id="knowledge">
          <div class="row" style="margin-bottom:8px;">
            <input id="q" class="grow" type="text" placeholder="Filter by title/category/path... (press / to focus)" oninput="quickFilter()" />
            <select id="sortMode" class="btn" onchange="sortRows()" style="padding:8px 10px;">
              <option value="title_asc">Sort: Title A→Z</option>
              <option value="title_desc">Sort: Title Z→A</option>
              <option value="size_desc">Sort: Size ↓</option>
              <option value="size_asc">Sort: Size ↑</option>
            </select>
            <button class="btn" onclick="clearFilters()">Clear</button>
          </div>
          <div class="chips">
            <button class="chip active" data-cat="all" onclick="setCategory('all', this)">All</button>
            <button class="chip" onclick="setCategory('Wikipedia', this)">Wikipedia</button>
            <button class="chip" onclick="setCategory('Medical', this)">Medical</button>
            <button class="chip" onclick="setCategory('Travel', this)">Travel</button>
            <button class="chip" onclick="setCategory('Dictionary', this)">Dictionary</button>
            <button class="chip" onclick="setCategory('Maps', this)">Maps</button>
            <button class="chip" onclick="setCategory('Other', this)">Other</button>
            <span class="muted" style="margin-left:8px;">Visible: <strong id="visibleCount">0</strong></span>
          </div>
          <div class="table">
            <table>
              <thead><tr><th>Title</th><th>Category</th><th>Size</th><th>Action</th><th>Path</th></tr></thead>
              <tbody>
                {% for z in zims %}
                <tr data-search="{{ (z.title + ' ' + z.category + ' ' + z.path).lower() }}" data-category="{{ z.category }}" data-title="{{ z.title.lower() }}" data-size-bytes="{{ z.size_bytes }}">
                  <td>{{ z.icon }} <strong>{{ z.title }}</strong><div class="muted">{{ z.filename }}</div></td>
                  <td><span class="badge">{{ z.category }}</span></td>
                  <td>{{ z.size }}</td>
                  <td>
                    <a class="btn" href="{{ z.open_url }}" target="_blank">Open</a>
                    <button class="btn" onclick='navigator.clipboard.writeText({{ z.open_url|tojson }})'>Copy Link</button>
                  </td>
                  <td class="muted">{{ z.path }}</td>
                </tr>
                {% endfor %}
              </tbody>
            </table>
          </div>
        </div>

        <div class="card" id="wiki-search">
          <h3 style="margin:0 0 8px;">Wiki Search</h3>
          <div class="row"><input id="wikiQ" class="grow" type="text" placeholder="Search active content (e.g., black holes)" /><button class="btn primary" type="button" onclick="wikiSearch()">Search</button></div>
          <div class="split" style="margin-top:10px;">
            <div style="border:1px solid var(--border);border-radius:10px;max-height:240px;overflow:auto;padding:6px;" id="wikiResults">
              {% if wiki_results and wiki_results|length > 0 %}
                {% for r in wiki_results %}
                  <div style="padding:8px;border-bottom:1px solid #24345d;">
                    <div><strong>{{ loop.index }}. {{ r.title }}</strong></div>
                    <div class="muted"><a href="{{ r.url }}" target="_blank">Open full article</a></div>
                    <button class="btn" style="margin-top:6px;" onclick='wikiParse({{ r.url|tojson }})'>Parse excerpt</button>
                  </div>
                {% endfor %}
              {% else %}
                <div class="muted">Run a query to see results.</div>
              {% endif %}
            </div>
            <div style="border:1px solid var(--border);border-radius:10px;max-height:240px;overflow:auto;padding:10px;white-space:pre-wrap;" id="wikiParsed"></div>
          </div>
        </div>
      </div>

      <div>
        <div class="card">
          <details>
            <summary style="cursor:pointer;font-weight:600;">Advanced System</summary>
            <p class="muted" style="margin:8px 0 8px;">{{ health_summary }}</p>
            <div class="row">
              <button class="btn" onclick="runAdminAction('doctor')">Health Check</button>
              <button class="btn" onclick="runAdminAction('verify')">Trust Verify</button>
              <button class="btn" onclick="runAdminAction('backup_usb')">Backup</button>
              <button class="btn" onclick="runAdminAction('sync_usb')">Import USB</button>
            </div>
            <pre id="adminOut" style="margin-top:8px;max-height:180px;overflow:auto;">Ready.</pre>
          </details>
        </div>

        <div class="card" id="translator">
          <h3 style="margin:0 0 8px;">Translator (Offline)</h3>
          <p class="muted" style="margin:0 0 10px;">One clean flow for both conversation and normal text translation.</p>
          <form id="translateForm" method="post" action="/translate_form">
            <div class="row">
              <select id="trSource" name="source">
                {% for c in language_options %}
                  <option value="{{ c.code }}" {% if c.code == tr_source %}selected{% endif %}>{{ c.label }}</option>
                {% endfor %}
              </select>
              <button class="btn" type="button" onclick="swapTranslatorLangs()">⇄</button>
              <select id="trTarget" name="target">
                {% for c in language_options %}
                  <option value="{{ c.code }}" {% if c.code == tr_target %}selected{% endif %}>{{ c.label }}</option>
                {% endfor %}
              </select>
            </div>
            <textarea id="trInput" name="text" style="margin-top:10px;" placeholder="Type what one person says (or paste any text)...">{{ tr_input }}</textarea>
            <div class="row" style="margin-top:6px;">
              <button class="btn primary" type="submit" formaction="/translate_form">Translate</button>
              <button class="btn" type="button" onclick="document.getElementById('trInput').value = document.getElementById('trOutput').value || ''">Use Output as Next Input</button>
            </div>
          </form>
          <textarea id="trOutput" style="margin-top:8px;" placeholder="Translation output..." readonly>{{ tr_output }}</textarea>
          <p id="trMeta" class="muted" style="margin:8px 0 0;">{{ tr_meta }}</p>
        </div>

        <div class="card">
          <h3 style="margin:0 0 8px;">CLI Quick Query</h3>
          <p class="muted">In terminal, run these exact commands:</p>
          <pre>source ~/wiki/.venv/bin/activate
wiki-ask "black holes"
wiki-ask "water purification" --top 5 --open 1 --chars 2500</pre>
        </div>
      </div>
    </div>
  </div>
</body>
</html>
"""

HELP_HTML = """
<!doctype html><html><head><meta charset='utf-8'><title>Offline Help</title><style>body{font-family:Inter,Arial,sans-serif;max-width:900px;margin:30px auto;padding:0 16px;color:#eaf0ff;background:#0b1020}h1,h2{color:#9ec0ff}code,pre{background:#13213f;padding:2px 6px;border-radius:6px}a{color:#7bb2ff}</style></head><body>
<h1>Offgrid Intel Kit – Help</h1>
<p>This system is designed to run without internet once installed.</p>
<h2>URLs</h2>
<ul><li>Dashboard: <code>:8090</code></li><li>Kiwix reader: <code>:8080</code></li><li>Offline maps: <code>:8091</code></li></ul>
<h2>Translator</h2>
<ul><li>Built for offline use with local translation engine(s)</li><li>If language packs are missing, install Argos Translate + package files and restart <code>zim-ui.service</code></li></ul>
<h2>USB Distribution</h2>
<ul><li>Run <code>START_LINUX.sh</code> (Linux), <code>START_WINDOWS.bat</code> (Windows), or <code>START_MAC.command</code> (macOS)</li><li>Use <code>scripts/verify_checksums.sh</code> before install</li></ul>
<h2>Troubleshooting</h2>
<ul><li>Check service status: <code>wiki-status</code>, <code>zim-ui-status</code>, <code>map-ui-status</code></li><li>Port check: <code>ss -ltnp | grep -E ':8080|:8090|:8091'</code></li></ul>
</body></html>
"""

EBOOKS_HTML = """
<!doctype html><html><head><meta charset='utf-8'><title>Offline Ebooks</title>
<style>
body{font-family:Inter,Arial,sans-serif;max-width:1100px;margin:24px auto;padding:0 16px;color:#eaf0ff;background:#0b1020}
h1{color:#9ec0ff} .muted{color:#a9b5d1}
.card{border:1px solid #2a3b63;background:#121a2b;border-radius:12px;padding:12px;margin-bottom:12px}
a{color:#7bb2ff}
.row{padding:8px;border-bottom:1px solid #27375f}
.path{font-size:12px;color:#9eb3df}
</style></head><body>
<h1>Offline Ebooks</h1>
<div class='card'>
  <div class='muted'>Drop ebooks into any of these folders:</div>
  <ul>__ROOTS_HTML__</ul>
</div>
<div class='card'>
  __ROWS_HTML__
</div>
</body></html>
"""

SETUP_HTML = """
<!doctype html><html><head><meta charset='utf-8'><title>Instant Personalize</title>
<style>
body{font-family:Inter,Arial,sans-serif;max-width:980px;margin:24px auto;padding:0 16px;color:#eaf0ff;background:#0b1020}
h1{color:#9ec0ff}.card{border:1px solid #2a3b63;background:#121a2b;border-radius:12px;padding:12px;margin-bottom:12px}
.muted{color:#a9b5d1}.btn{border:1px solid #2a3b63;border-radius:10px;padding:8px 12px;background:#1d2f57;color:#e7edff;cursor:pointer}
pre{border:1px solid #2a3b63;background:#0f1830;border-radius:10px;padding:10px;white-space:pre-wrap}
</style>
<script>
async function runStep(action){
  const out=document.getElementById('out');
  out.textContent='Working on it…';
  const r=await fetch('/api/admin/action',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({action})});
  const d=await r.json();
  out.textContent=(d.ok?'✅ ':'⚠️ ')+(d.message||'')+'\n\n'+(d.output||'');
}
</script>
</head><body>
<h1>Instant Personalize</h1>
<div class='card'>
  <p class='muted'>You’re already live. Use these one-tap actions to personalize and verify your system in under a minute.</p>
  <button class='btn' onclick="runStep('setup_dirs')">1) Prepare My Library</button>
  <button class='btn' onclick="runStep('doctor')">2) Run Confidence Check</button>
  <button class='btn' onclick="runStep('verify')">3) Verify Bundle Integrity</button>
  <button class='btn' onclick="runStep('sync_usb')">4) Import My USB Content</button>
</div>
<div class='card'><pre id='out'>Ready. Press step 1.</pre></div>
</body></html>
"""

MORSE_HTML = """
<!doctype html><html><head><meta charset='utf-8'><title>Morse Tool</title>
<style>
body{font-family:Inter,Arial,sans-serif;max-width:900px;margin:24px auto;padding:0 16px;color:#eaf0ff;background:#0b1020}
h1{color:#9ec0ff}.card{border:1px solid #2a3b63;background:#121a2b;border-radius:12px;padding:12px;margin-bottom:12px}
textarea,input{width:100%;padding:9px;border-radius:10px;border:1px solid #2a3b63;background:#0f1830;color:#eaf0ff}
.btn{border:1px solid #2a3b63;border-radius:10px;padding:8px 12px;background:#1d2f57;color:#e7edff;cursor:pointer}
.flash{height:30px;border-radius:8px;background:#18284e;margin-top:8px}
</style>
<script>
const MAP = {
  'A':'.-','B':'-...','C':'-.-.','D':'-..','E':'.','F':'..-.','G':'--.','H':'....','I':'..','J':'.---','K':'-.-','L':'.-..','M':'--','N':'-.','O':'---','P':'.--.','Q':'--.-','R':'.-.','S':'...','T':'-','U':'..-','V':'...-','W':'.--','X':'-..-','Y':'-.--','Z':'--..',
  '0':'-----','1':'.----','2':'..---','3':'...--','4':'....-','5':'.....','6':'-....','7':'--...','8':'---..','9':'----.',' ':'/'
};
const REV = Object.fromEntries(Object.entries(MAP).map(([k,v])=>[v,k]));
function enc(){
  const t=(document.getElementById('plain').value||'').toUpperCase();
  document.getElementById('morse').value=[...t].map(ch=>MAP[ch]||'').filter(Boolean).join(' ');
}
function dec(){
  const m=(document.getElementById('morse').value||'').trim().split(/\\s+/);
  document.getElementById('plain').value=m.map(x=>REV[x]||'?').join('').replaceAll('/',' ');
}
async function play(){
  const txt=(document.getElementById('morse').value||'').trim();
  if(!txt) return;
  const ctx=new (window.AudioContext||window.webkitAudioContext)();
  const flash=document.getElementById('flash');
  const dot=0.08;
  const sleep=(ms)=>new Promise(r=>setTimeout(r,ms));
  for(const ch of txt){
    if(ch==='.'||ch==='-'){
      const dur=(ch==='.')?dot:dot*3;
      const o=ctx.createOscillator(); const g=ctx.createGain();
      o.type='sine'; o.frequency.value=700; o.connect(g); g.connect(ctx.destination);
      g.gain.value=0.2; o.start(); flash.style.background='#7bb2ff';
      await sleep(dur*1000); o.stop(); flash.style.background='#18284e';
      await sleep(dot*1000);
    } else if(ch===' ') {
      await sleep(dot*2*1000);
    } else if(ch==='/') {
      await sleep(dot*6*1000);
    }
  }
}
</script></head><body>
<h1>Morse Tool</h1>
<div class='card'>
  <textarea id='plain' placeholder='Plain text'></textarea>
  <div style='margin-top:8px;display:flex;gap:8px;flex-wrap:wrap'>
    <button class='btn' onclick='enc()'>Encode → Morse</button>
    <button class='btn' onclick='dec()'>Decode → Text</button>
    <button class='btn' onclick='play()'>Play Signal</button>
  </div>
  <textarea id='morse' style='margin-top:8px' placeholder='Morse code'></textarea>
  <div id='flash' class='flash'></div>
</div>
</body></html>
"""

LANGUAGE_LABELS = {
    "auto": "Auto Detect",
    "en": "English",
    "es": "Spanish",
    "fr": "French",
    "de": "German",
    "it": "Italian",
    "pt": "Portuguese",
    "ru": "Russian",
    "uk": "Ukrainian",
    "ar": "Arabic",
    "hi": "Hindi",
    "ja": "Japanese",
    "ko": "Korean",
    "zh": "Chinese",
}


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
    # 1) collect unique real paths
    by_path = {}
    for root in roots:
        for p in root.rglob("*.zim"):
            try:
                by_path[str(p.resolve())] = p
            except Exception:
                continue

    # 2) collapse mirrored duplicates (same ZIM stem from different roots)
    # prefer larger file when duplicates exist
    by_stem = {}
    for p in by_path.values():
        try:
            key = p.stem.lower()
            size = p.stat().st_size if p.exists() else 0
        except Exception:
            key, size = p.stem.lower(), 0

        if key not in by_stem:
            by_stem[key] = p
            continue

        cur = by_stem[key]
        try:
            cur_size = cur.stat().st_size if cur.exists() else 0
        except Exception:
            cur_size = 0

        if size > cur_size:
            by_stem[key] = p

    return sorted(by_stem.values(), key=lambda p: str(p).lower())


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


def kiwix_content_map():
    out = {}
    try:
        r = requests.get(f"{KIWIX_BASE}/catalog/v2/entries?count=100", timeout=20)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "xml")
        for entry in soup.find_all("entry"):
            title = (entry.find("title").get_text(" ", strip=True) if entry.find("title") else "").strip()
            href = ""
            for link in entry.find_all("link"):
                h = (link.get("href") or "").strip()
                if h.startswith("/content/"):
                    href = h
                    break
            if title and href:
                out[title.lower()] = href
    except Exception:
        pass
    return out


def resolve_open_href(filename: str, title: str, content_map: dict):
    n = filename.lower()
    t = title.lower()

    # direct title match from catalog
    if t in content_map:
        return content_map[t]

    # fallback keyword matching
    prefs = []
    if "wikipedia" in n:
        prefs += ["wikipedia"]
    if "wikem" in n or "medicine" in n:
        prefs += ["wikimed", "medical", "wikimedicine"]
    if "openstreetmap" in n or "osm" in n or "map" in n:
        prefs += ["openstreetmap", "map"]
    if "stack" in n:
        prefs += ["stack", "overflow"]

    for key in prefs:
        for k, href in content_map.items():
            if key in k:
                return href

    # final fallback (may fail for renamed files)
    return f"/content/{quote(Path(filename).stem)}"


def preferred_search_content_id():
    """Pick a single content id so Kiwix search doesn't fail in multi-language setups."""
    cmap = kiwix_content_map()
    if not cmap:
        return "wikipedia"

    hrefs = list(cmap.values())

    # prefer practical emergency-friendly sources first
    for preferred in ["wikimedicine", "wikipedia", "openstreetmap", "stackoverflow"]:
        for h in hrefs:
            if f"/content/{preferred}" in h:
                return preferred

    # fallback: first available /content/<id>
    for h in hrefs:
        if h.startswith("/content/"):
            return h.split("/content/", 1)[1].split("/", 1)[0]

    return "wikipedia"


def wiki_search(query: str, limit: int = 8):
    content_id = preferred_search_content_id()
    r = requests.get(
        f"{KIWIX_BASE}/search",
        params={"content": content_id, "pattern": query},
        timeout=20,
    )
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


def _map_lang(code: str) -> str:
    if not code:
        return "en"
    c = code.lower().strip()
    if c == "zh":
        return "zh"
    return c.split("-")[0]


def _detect_lang_simple(text: str) -> str:
    try:
        from langdetect import detect
        return _map_lang(detect(text))
    except Exception:
        return "en"


def offline_translate(text: str, source: str, target: str):
    source = _map_lang(source)
    target = _map_lang(target)
    if source == "auto":
        source = _detect_lang_simple(text)

    try:
        import argostranslate.translate as argos_translate
        installed_languages = argos_translate.get_installed_languages()
        by_code = {l.code: l for l in installed_languages}
        from_lang = by_code.get(source)
        to_lang = by_code.get(target)

        if not from_lang or not to_lang:
            return {
                "translation": "",
                "detected": source,
                "engine": "offline-unavailable",
                "error": f"Missing language pack for {source} → {target}. Install Argos package(s).",
            }

        # 1) Direct path if available
        try:
            translation = from_lang.get_translation(to_lang)
            translated = translation.translate(text)
            return {
                "translation": translated,
                "detected": source,
                "engine": "argos-local",
                "confidence": None,
            }
        except Exception:
            pass

        # 2) Pivot path via English if direct pair missing
        pivot = by_code.get("en")
        if pivot and source != "en" and target != "en":
            try:
                first = from_lang.get_translation(pivot).translate(text)
                second = pivot.get_translation(to_lang).translate(first)
                return {
                    "translation": second,
                    "detected": source,
                    "engine": "argos-local-pivot-en",
                    "confidence": None,
                }
            except Exception:
                pass

        return {
            "translation": "",
            "detected": source,
            "engine": "offline-unavailable",
            "error": f"No installed translation path for {source} → {target}.",
        }
    except Exception as e:
        return {
            "translation": "",
            "detected": source,
            "engine": "offline-unavailable",
            "error": f"Offline translator not ready: {e}",
        }


def translator_status_text():
    try:
        import argostranslate.translate as argos_translate
        langs = [l.code for l in argos_translate.get_installed_languages()]
        if len(langs) >= 2:
            return f"Translator online (local Argos: {', '.join(langs[:6])}{'…' if len(langs) > 6 else ''})", False
        return "Translator limited (install more local language packs)", True
    except Exception:
        return "Translator offline-ready but packages not installed", True


def language_options_for_installed():
    options = [{"code": "auto", "label": LANGUAGE_LABELS.get("auto", "Auto Detect")}]
    try:
        import argostranslate.translate as argos_translate
        installed = sorted({l.code for l in argos_translate.get_installed_languages()})
        for c in installed:
            options.append({"code": c, "label": LANGUAGE_LABELS.get(c, c.upper())})
    except Exception:
        # fallback to known defaults if translator libs unavailable
        for c in ["en", "es", "fr"]:
            options.append({"code": c, "label": LANGUAGE_LABELS.get(c, c.upper())})
    return options


def _ebook_roots_existing():
    roots = []
    for r in EBOOK_ROOTS:
        try:
            rr = r.expanduser().resolve()
        except Exception:
            rr = r.expanduser()

        # Only auto-create inside home paths; external roots are optional.
        try:
            if str(rr).startswith(str(Path.home())):
                rr.mkdir(parents=True, exist_ok=True)
            elif not rr.exists():
                continue
        except Exception:
            continue

        roots.append(rr)
    return roots


def list_ebooks(limit: int = 500):
    roots = _ebook_roots_existing()
    out = []
    seen = set()
    for root in roots:
        for p in root.rglob('*'):
            if not p.is_file() or p.suffix.lower() not in EBOOK_EXTS:
                continue
            rp = str(p.resolve())
            if rp in seen:
                continue
            seen.add(rp)
            out.append({
                'name': p.name,
                'path': rp,
                'size': format_size(p.stat().st_size if p.exists() else 0),
            })
            if len(out) >= limit:
                return roots, sorted(out, key=lambda x: x['name'].lower())
    return roots, sorted(out, key=lambda x: x['name'].lower())


def _is_under_roots(path: Path, roots):
    try:
        rp = path.resolve()
    except Exception:
        return False
    for root in roots:
        try:
            rp.relative_to(root)
            return True
        except Exception:
            continue
    return False


def health_summary_text():
    statuses = []
    for svc in ["kiwix.service", "zim-selector.service", "offline-map-ui.service"]:
        try:
            subprocess.check_call(["systemctl", "is-active", "--quiet", svc])
            statuses.append(f"{svc.split('.')[0]}:ok")
        except Exception:
            statuses.append(f"{svc.split('.')[0]}:check")
    if (RUNTIME_ROOT / "ebooks").exists():
        statuses.append("ebooks:ok")
    else:
        statuses.append("ebooks:missing")
    return " • ".join(statuses)


def run_admin_action(action: str):
    root = KIT_ROOT
    scripts = root / "scripts"

    def run(cmd, timeout=120):
        try:
            p = subprocess.run(cmd, cwd=str(root), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=timeout)
            out = (p.stdout or "")[-4000:]
            return (p.returncode == 0), out
        except subprocess.TimeoutExpired:
            return False, "Action timed out. Please try again."
        except Exception as e:
            return False, f"Action failed: {e}"

    if action == "doctor":
        ok, out = run(["bash", str(scripts / "doctor.sh")], timeout=90)
        return ok, ("Health check completed" if ok else "Health check found issues"), out
    if action == "verify":
        ok, out = run(["bash", str(scripts / "verify_checksums.sh")], timeout=90)
        return ok, ("Integrity verified" if ok else "Integrity check failed"), out
    if action == "backup_usb":
        usb_base = Path(os.environ.get("WIKI_USB_ROOT", "/media/void/94AA7041AA7021C2/OfflineKnowledgeKit"))
        if not usb_base.exists():
            return False, "Backup drive not connected", str(usb_base)
        if not os.access(str(usb_base), os.W_OK):
            return False, "Backup drive not writable", f"No write permission: {usb_base}"
        ok, out = run(["bash", str(scripts / "sync_external_drive.sh")], timeout=180)
        return ok, ("Backup completed" if ok else "Backup failed"), out
    if action == "sync_usb":
        usb_root = Path(os.environ.get("WIKI_USB_ROOT", "/media/void/94AA7041AA7021C2/OfflineKnowledgeKit"))
        usb = usb_root / "wiki-offline-pi-kit/zims"
        if not usb.exists():
            return False, "USB content not found", str(usb)
        ok, out = run(["bash", str(scripts / "import_zims_from_usb.sh"), str(usb)], timeout=180)
        return ok, ("USB import completed" if ok else "USB import failed"), out
    if action == "setup_dirs":
        created = []
        for p in [RUNTIME_ROOT / "ebooks", root / "ebooks", RUNTIME_ROOT / "zim"]:
            p.mkdir(parents=True, exist_ok=True)
            created.append(str(p))
        return True, "Library folders ready", "\n".join(created)
    return False, "Unknown action", action


def build_page(extra_scan_dir: str, do_resync: bool, tr_input: str = "", tr_source: str = "en", tr_target: str = "es", tr_output: str = "", tr_meta: str = "", wiki_results=None, qa_status: str = ""):
    roots = build_roots(extra_scan_dir)
    paths = scan_zims(roots)
    sync_msg = sync_all_loaded(paths) if do_resync else ""

    zims, total_size = [], 0
    ip = host_ip()
    cmap = kiwix_content_map()
    for p in paths:
        size_raw = p.stat().st_size if p.exists() else 0
        total_size += size_raw
        category, icon = classify(p.name)
        ztitle = pretty_title(p.name)
        href = resolve_open_href(p.name, ztitle, cmap)
        if href.startswith('/'):
            open_url = f"http://{ip}:8080{href}"
        else:
            open_url = href
        zims.append({
            "path": str(p),
            "filename": p.name,
            "zim_id": p.stem,
            "title": ztitle,
            "icon": icon,
            "category": category,
            "size": format_size(size_raw),
            "size_bytes": size_raw,
            "open_url": open_url,
        })

    status, warning = translator_status_text()
    health_summary = health_summary_text()
    language_options = language_options_for_installed()

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
        language_options=language_options,
        translator_status=status,
        translator_offline_warning=warning,
        health_summary=health_summary,
        tr_input=tr_input,
        tr_source=tr_source,
        tr_target=tr_target,
        tr_output=tr_output,
        tr_meta=tr_meta,
        wiki_results=wiki_results or [],
        qa_status=qa_status,
    )


@app.get("/")
def index():
    scan_dir = request.args.get("scan_dir", "")
    do_resync = request.args.get("resync", "1") == "1"
    tr_input = request.args.get("tr_input", "")
    tr_source = request.args.get("tr_source", "en")
    tr_target = request.args.get("tr_target", "es")
    tr_output = request.args.get("tr_output", "")
    tr_meta = request.args.get("tr_meta", "")

    qa = (request.args.get("qa") or "").strip().lower()
    wiki_results = []
    qa_status = ""
    if qa in {"water", "firstaid", "shelter"}:
        qmap = {
            "water": "water purification",
            "firstaid": "first aid",
            "shelter": "shelter building",
        }
        q = qmap[qa]
        try:
            wiki_results = wiki_search(q)
            qa_status = f"Showing results for: {q}"
        except Exception:
            qa_status = f"Search failed for: {q}"
    elif qa == "translate":
        tr_input = tr_input or "I need medical help"
        tr_source = tr_source or "en"
        tr_target = tr_target or "es"
        qa_status = "Prepared emergency phrase in translator."

    return build_page(scan_dir, do_resync, tr_input, tr_source, tr_target, tr_output, tr_meta, wiki_results, qa_status)


@app.get("/help")
def help_page():
    return HELP_HTML


@app.get("/setup")
def setup_page():
    return SETUP_HTML


@app.get("/go/knowledge")
def go_knowledge():
    return redirect(f"http://{host_ip()}:8080")


@app.get("/go/maps")
def go_maps():
    return redirect(f"http://{host_ip()}:8091")


@app.get("/go/translate")
def go_translate():
    return redirect('/#translator')


@app.get("/go/library")
def go_library():
    return redirect('/ebooks')


@app.get("/go/water")
def go_water():
    cid = preferred_search_content_id()
    return redirect(f"http://{host_ip()}:8080/search?content={quote(cid)}&pattern=water%20purification")


@app.get("/go/firstaid")
def go_firstaid():
    cid = preferred_search_content_id()
    return redirect(f"http://{host_ip()}:8080/search?content={quote(cid)}&pattern=first%20aid")


@app.get("/go/shelter")
def go_shelter():
    cid = preferred_search_content_id()
    return redirect(f"http://{host_ip()}:8080/search?content={quote(cid)}&pattern=shelter%20building")


@app.get("/go/emergency-phrase")
def go_emergency_phrase():
    return redirect('/?qa=translate#translator')


@app.get("/morse")
def morse_page():
    return MORSE_HTML


@app.get("/health")
def health_page():
    summary = health_summary_text()
    return jsonify({"summary": summary})


@app.post("/api/admin/action")
def api_admin_action():
    payload = request.get_json(silent=True) or {}
    action = (payload.get("action") or "").strip()
    ok, message, output = run_admin_action(action)
    code = 200 if ok else 400
    return jsonify({"ok": ok, "message": message, "output": output}), code


@app.get("/ebooks")
def ebooks_page():
    roots, files = list_ebooks()
    roots_html = ''.join(f"<li><code>{str(r)}</code></li>" for r in roots)
    if files:
        rows_html = ''.join(
            f"<div class='row'><a href='/ebooks/file?path={quote(f['path'])}' target='_blank'>{f['name']}</a>"
            f" <span class='muted'>({f['size']})</span><div class='path'>{f['path']}</div></div>"
            for f in files
        )
    else:
        rows_html = "<div class='muted'>No ebooks found yet. Add files to one of the ebook folders above.</div>"
    return EBOOKS_HTML.replace('__ROOTS_HTML__', roots_html).replace('__ROWS_HTML__', rows_html)


@app.get("/ebooks/file")
def ebooks_file():
    raw = (request.args.get("path") or "").strip()
    if not raw:
        return abort(400)
    p = Path(raw).expanduser()
    roots = _ebook_roots_existing()
    if not p.exists() or not p.is_file() or p.suffix.lower() not in EBOOK_EXTS:
        return abort(404)
    if not _is_under_roots(p, roots):
        return abort(403)
    return send_file(str(p), conditional=True)


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


@app.post("/translate_form")
def translate_form():
    text = (request.form.get("text") or "").strip()
    source = (request.form.get("source") or "auto").strip()
    target = (request.form.get("target") or "en").strip()
    tr_output = ""
    tr_meta = ""

    if text and target:
        result = offline_translate(text, source, target)
        if result.get("error"):
            tr_meta = result.get("error")
        else:
            tr_output = result.get("translation", "")
            tr_meta = f"engine: {result.get('engine','offline')} • detected: {result.get('detected', source)}"
    elif not text:
        tr_meta = "Enter text to translate."

    qs = urlencode({
        "resync": "0",
        "tr_input": text,
        "tr_source": source,
        "tr_target": target,
        "tr_output": tr_output,
        "tr_meta": tr_meta,
    })
    from flask import redirect
    return redirect(f"/?{qs}#translator")


@app.post("/api/translate")
def api_translate():
    payload = request.get_json(silent=True) or {}
    text = (payload.get("text") or "").strip()
    source = (payload.get("source") or "auto").strip()
    target = (payload.get("target") or "en").strip()

    if not text:
        return jsonify({"error": "Text is required.", "translation": ""}), 400
    if not target:
        return jsonify({"error": "Target language is required.", "translation": ""}), 400

    result = offline_translate(text, source, target)
    if result.get("error"):
        return jsonify(result), 503
    return jsonify(result)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8090)
