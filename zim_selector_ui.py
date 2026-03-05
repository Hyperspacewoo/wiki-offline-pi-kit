#!/usr/bin/env python3
from flask import Flask, request, redirect, url_for, render_template_string
from pathlib import Path
import subprocess

app = Flask(__name__)

LIST_FILE = Path.home() / "wiki/data/active_zims.txt"
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
  <title>Kiwix Content Manager</title>
  <style>
    :root {
      --bg: #0b1020;
      --panel: #121a30;
      --panel2: #16223e;
      --text: #eaf0ff;
      --muted: #a9b5d1;
      --accent: #62a4ff;
      --ok: #2ad59b;
      --border: #2a3b63;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: Inter, Segoe UI, Roboto, Helvetica, Arial, sans-serif;
      background: radial-gradient(1200px 600px at 10% -20%, #243b70 0, transparent 60%), var(--bg);
      color: var(--text);
    }
    .wrap { max-width: 1220px; margin: 0 auto; padding: 22px; }
    .hero {
      border: 1px solid var(--border);
      background: linear-gradient(180deg, #16244a, #111a33);
      border-radius: 16px;
      padding: 18px;
      margin-bottom: 14px;
      box-shadow: 0 8px 28px rgba(0,0,0,.28);
    }
    .title { font-size: 24px; font-weight: 700; margin: 0 0 6px; }
    .subtitle { color: var(--muted); margin: 0; }
    .grid { display: grid; grid-template-columns: 1fr 1fr 1fr 1fr; gap: 10px; margin-top: 14px; }
    .stat { border: 1px solid var(--border); background: rgba(255,255,255,0.02); border-radius: 12px; padding: 10px; }
    .stat .k { color: var(--muted); font-size: 12px; }
    .stat .v { font-size: 20px; font-weight: 700; margin-top: 2px; }

    .card {
      border: 1px solid var(--border);
      background: linear-gradient(180deg, var(--panel), var(--panel2));
      border-radius: 14px;
      padding: 14px;
      margin-bottom: 12px;
      box-shadow: 0 6px 22px rgba(0,0,0,.2);
    }

    .row { display: flex; gap: 8px; flex-wrap: wrap; align-items: center; }
    .grow { flex: 1; }

    input[type=text] {
      width: 100%;
      padding: 10px 12px;
      border: 1px solid var(--border);
      border-radius: 10px;
      background: #0f1830;
      color: var(--text);
      outline: none;
    }

    .btn {
      border: 1px solid var(--border);
      background: #1d2f57;
      color: #e7edff;
      border-radius: 10px;
      padding: 9px 12px;
      cursor: pointer;
      font-weight: 600;
    }
    .btn:hover { filter: brightness(1.1); }
    .btn.primary { background: linear-gradient(180deg, #4f8fff, #3b73d7); border-color: #6aa2ff; }
    .btn.ok { background: linear-gradient(180deg, #2dcf97, #1ea675); border-color: #40dfa7; }
    .btn.ghost { background: #142240; }

    .chips { display: flex; gap: 8px; flex-wrap: wrap; }
    .chip {
      border: 1px solid var(--border);
      border-radius: 999px;
      padding: 6px 10px;
      color: var(--muted);
      font-size: 12px;
      background: rgba(255,255,255,0.02);
    }

    .muted { color: var(--muted); font-size: 13px; }
    .msg { padding: 10px; border-radius: 10px; background: rgba(98,164,255,.15); border: 1px solid #3f66b8; margin-top: 8px; }

    .table { max-height: 58vh; overflow: auto; border: 1px solid var(--border); border-radius: 12px; }
    table { width: 100%; border-collapse: collapse; min-width: 900px; }
    th, td { padding: 10px; border-bottom: 1px solid #24345d; text-align: left; font-size: 14px; }
    th { position: sticky; top: 0; background: #172549; z-index: 1; }
    tr:hover td { background: rgba(98,164,255,0.08); }

    .badge { font-size: 11px; border-radius: 999px; padding: 3px 8px; border: 1px solid var(--border); color: #c9d5f5; }
    a { color: #8fc0ff; text-decoration: none; }
    a:hover { text-decoration: underline; }

    @media (max-width: 900px) {
      .grid { grid-template-columns: 1fr 1fr; }
    }
  </style>
  <script>
    function quickFilter() {
      const q = (document.getElementById('q').value || '').toLowerCase();
      document.querySelectorAll('tbody tr[data-search]').forEach(tr => {
        tr.style.display = tr.dataset.search.includes(q) ? '' : 'none';
      });
    }
    function selectVisible(flag) {
      document.querySelectorAll('tbody tr').forEach(tr => {
        if (tr.style.display === 'none') return;
        const cb = tr.querySelector('input[type=checkbox]');
        if (cb) cb.checked = flag;
      });
    }
  </script>
</head>
<body>
  <div class="wrap">
    <div class="hero">
      <h1 class="title">Kiwix Content Manager</h1>
      <p class="subtitle">Enterprise-grade dashboard for managing offline knowledge libraries and map access.</p>
      <div class="grid">
        <div class="stat"><div class="k">Total ZIM files discovered</div><div class="v">{{ total }}</div></div>
        <div class="stat"><div class="k">Currently active</div><div class="v">{{ active_count }}</div></div>
        <div class="stat"><div class="k">Storage footprint</div><div class="v">{{ total_size }}</div></div>
        <div class="stat"><div class="k">Data roots scanned</div><div class="v">{{ roots_count }}</div></div>
      </div>
    </div>

    <div class="card">
      <form method="post" action="/scan">
        <div class="row">
          <div class="grow">
            <input type="text" name="scan_dir" placeholder="Optional extra folder to include (example: /media/usb/zim)" value="{{ scan_dir }}" />
          </div>
          <button class="btn" type="submit">Rescan All Sources</button>
        </div>
      </form>
      <div class="chips" style="margin-top:8px;">
        {% for r in roots %}<span class="chip">{{ r }}</span>{% endfor %}
      </div>
      <p class="muted" style="margin-top:8px;">This view always includes all known roots by default, plus your optional extra folder.</p>
    </div>

    <div class="card">
      <div class="row">
        <form method="post" action="/apply_profile"><input type="hidden" name="scan_dir" value="{{ scan_dir }}" /><input type="hidden" name="profile" value="all" /><button class="btn" type="submit">📚 Activate All</button></form>
        <form method="post" action="/apply_profile"><input type="hidden" name="scan_dir" value="{{ scan_dir }}" /><input type="hidden" name="profile" value="general" /><button class="btn" type="submit">📘 General</button></form>
        <form method="post" action="/apply_profile"><input type="hidden" name="scan_dir" value="{{ scan_dir }}" /><input type="hidden" name="profile" value="medical" /><button class="btn" type="submit">🩺 Medical</button></form>
        <form method="post" action="/apply_profile"><input type="hidden" name="scan_dir" value="{{ scan_dir }}" /><input type="hidden" name="profile" value="maps" /><button class="btn" type="submit">🗺️ Maps</button></form>
      </div>
    </div>

    <div class="card">
      <div class="row" style="margin-bottom:8px;">
        <input id="q" class="grow" type="text" placeholder="Filter table by title, filename, category, or path..." oninput="quickFilter()" />
        <button class="btn ghost" type="button" onclick="selectVisible(true)">Select Visible</button>
        <button class="btn ghost" type="button" onclick="selectVisible(false)">Unselect Visible</button>
      </div>

      <form method="post" action="/apply">
        <input type="hidden" name="scan_dir" value="{{ scan_dir }}" />
        <div class="table">
          <table>
            <thead>
              <tr><th style="width:70px;">Use</th><th>Title</th><th>Category</th><th>Size</th><th>Filename</th><th>Path</th></tr>
            </thead>
            <tbody>
              {% for z in zims %}
              <tr data-search="{{ (z.title + ' ' + z.filename + ' ' + z.path + ' ' + z.category).lower() }}">
                <td><input type="checkbox" name="selected" value="{{ z.path }}" {% if z.path in active %}checked{% endif %}></td>
                <td>{{ z.icon }} <strong>{{ z.title }}</strong></td>
                <td><span class="badge">{{ z.category }}</span></td>
                <td>{{ z.size }}</td>
                <td>{{ z.filename }}</td>
                <td class="muted">{{ z.path }}</td>
              </tr>
              {% endfor %}
            </tbody>
          </table>
        </div>
        <div class="row" style="margin-top:10px;">
          <button class="btn ok" type="submit">Apply Selection + Restart Kiwix</button>
          <a class="btn" href="http://{{ host_ip }}:8080">Open Kiwix Reader</a>
          <a class="btn" href="http://{{ host_ip }}:8091">Open Offline Map</a>
        </div>
      </form>

      {% if msg %}<div class="msg">{{ msg }}</div>{% endif %}
      <p class="muted" style="margin-top:8px;">Active list file: {{ list_file }}</p>
    </div>
  </div>
</body>
</html>
"""


def format_size(n: int) -> str:
    units = ["B", "KB", "MB", "GB", "TB"]
    x = float(n)
    for u in units:
        if x < 1024 or u == units[-1]:
            return f"{x:.1f} {u}" if u != "B" else f"{int(x)} B"
        x /= 1024
    return f"{n} B"


def read_active():
    if not LIST_FILE.exists():
        return []
    return [line.strip() for line in LIST_FILE.read_text().splitlines() if line.strip() and not line.strip().startswith("#")]


def build_roots(extra: str):
    roots = []
    for p in DEFAULT_ROOTS:
        if p.exists() and p.is_dir():
            roots.append(p)
    if extra:
        ep = Path(extra)
        if ep.exists() and ep.is_dir() and ep not in roots:
            roots.append(ep)
    # dedupe preserving order
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
                rp = str(p.resolve())
                files[rp] = p
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


def build_profile_sets(paths):
    def match(*keys):
        keys = tuple(k.lower() for k in keys)
        return [p for p in paths if any(k in p.name.lower() for k in keys)]

    medical = match("wikem", "medicine", "medical", "med")
    maps = match("openstreetmap", "osm", "map")
    general = match("wikipedia", "wikivoyage", "wiktionary")
    profiles = {
        "all": paths,
        "general": general,
        "medical": medical,
        "maps": maps,
    }
    return profiles


def host_ip():
    try:
        out = subprocess.check_output(["hostname", "-I"], text=True).strip().split()
        return out[0] if out else "<PI_IP>"
    except Exception:
        return "<PI_IP>"


def restart_kiwix():
    try:
        subprocess.check_call(["sudo", "-n", "systemctl", "restart", "kiwix.service"])
        return "Updated selection and restarted kiwix.service"
    except subprocess.CalledProcessError:
        return (
            "Saved selection, but restart failed (sudo non-interactive denied or service issue). "
            "Run ./setup_sudoers_for_zim_ui.sh once, then try again."
        )
    except Exception as e:
        return f"Saved selection, but restart failed: {e}"


def build_page(extra_scan_dir: str, msg: str | None = None):
    roots = build_roots(extra_scan_dir)
    paths = scan_zims(roots)
    active = read_active()

    zims = []
    total_size_raw = 0
    for p in paths:
        try:
            size_raw = p.stat().st_size
        except Exception:
            size_raw = 0
        total_size_raw += size_raw
        category, icon = classify(p.name)
        zims.append(
            {
                "path": str(p),
                "filename": p.name,
                "title": pretty_title(p.name),
                "icon": icon,
                "category": category,
                "size": format_size(size_raw),
            }
        )

    return render_template_string(
        HTML,
        zims=zims,
        total=len(zims),
        total_size=format_size(total_size_raw),
        active=active,
        active_count=len(active),
        roots=[str(r) for r in roots],
        roots_count=len(roots),
        scan_dir=extra_scan_dir,
        list_file=str(LIST_FILE),
        host_ip=host_ip(),
        msg=msg,
    )


@app.get("/")
def index():
    scan_dir = request.args.get("scan_dir", "")
    return build_page(scan_dir, request.args.get("msg"))


@app.post("/scan")
def scan():
    scan_dir = (request.form.get("scan_dir") or "").strip()
    return redirect(url_for("index", scan_dir=scan_dir))


@app.post("/apply")
def apply():
    selected = request.form.getlist("selected")
    scan_dir = (request.form.get("scan_dir") or "").strip()
    if not selected:
        return redirect(url_for("index", msg="Select at least one ZIM.", scan_dir=scan_dir))

    LIST_FILE.parent.mkdir(parents=True, exist_ok=True)
    LIST_FILE.write_text("\n".join(selected) + "\n")
    msg = restart_kiwix()
    return redirect(url_for("index", msg=msg, scan_dir=scan_dir))


@app.post("/apply_profile")
def apply_profile():
    scan_dir = (request.form.get("scan_dir") or "").strip()
    chosen = (request.form.get("profile") or "").strip().lower()
    roots = build_roots(scan_dir)
    paths = scan_zims(roots)
    profiles = build_profile_sets(paths)

    if chosen not in profiles:
        return redirect(url_for("index", msg="Profile not found.", scan_dir=scan_dir))

    selected = [str(p) for p in profiles[chosen]]
    if not selected:
        return redirect(url_for("index", msg="That profile has no matching ZIMs.", scan_dir=scan_dir))

    LIST_FILE.parent.mkdir(parents=True, exist_ok=True)
    LIST_FILE.write_text("\n".join(selected) + "\n")
    msg = f"Applied profile '{chosen}' with {len(selected)} ZIM(s). " + restart_kiwix()
    return redirect(url_for("index", msg=msg, scan_dir=scan_dir))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8090)
