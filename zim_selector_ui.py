#!/usr/bin/env python3
from flask import Flask, request, redirect, url_for, render_template_string
from pathlib import Path
import subprocess

app = Flask(__name__)

LIST_FILE = Path.home() / "wiki/data/active_zims.txt"
SCAN_DIR_DEFAULT = Path("/mnt/wiki-ssd")

HTML = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <title>Kiwix ZIM Selector</title>
  <style>
    body { font-family: sans-serif; margin: 24px; max-width: 1000px; }
    .card { border: 1px solid #ddd; border-radius: 10px; padding: 16px; margin: 12px 0; }
    .muted { color: #555; font-size: 14px; }
    button { padding: 8px 14px; border-radius: 8px; border: 1px solid #aaa; background: #f8f8f8; cursor: pointer; }
    input[type=text] { width: 100%; padding: 8px; }
    .zim { display: flex; align-items: center; gap: 8px; margin: 8px 0; }
    .icon { width: 24px; text-align: center; }
    .meta { color: #555; font-size: 13px; margin-left: 32px; }
    .row { display: flex; gap: 8px; flex-wrap: wrap; }
  </style>
</head>
<body>
  <h2>Kiwix ZIM Selector</h2>
  <p class="muted">Choose which ZIMs Kiwix serves on port 8080.</p>

  <div class="card">
    <form method="post" action="/scan">
      <label>Scan folder for .zim files:</label>
      <input type="text" name="scan_dir" value="{{ scan_dir }}" />
      <p><button type="submit">Scan</button></p>
    </form>
  </div>

  <div class="card">
    <h3>Quick Profiles</h3>
    <p class="muted">One-click presets built from your current ZIM folder scan.</p>
    {% if profiles %}
      <div class="row">
        {% for p in profiles %}
          <form method="post" action="/apply_profile">
            <input type="hidden" name="scan_dir" value="{{ scan_dir }}" />
            <input type="hidden" name="profile" value="{{ p.name }}" />
            <button type="submit">{{ p.label }} ({{ p.count }})</button>
          </form>
        {% endfor %}
      </div>
    {% else %}
      <p class="muted">No profile candidates yet.</p>
    {% endif %}
  </div>

  <div class="card">
    <form method="post" action="/apply">
      <input type="hidden" name="scan_dir" value="{{ scan_dir }}" />
      {% if zims %}
        {% for z in zims %}
          <div class="zim">
            <span class="icon">{{ z.icon }}</span>
            <label><input type="checkbox" name="selected" value="{{ z.path }}" {% if z.path in active %}checked{% endif %}> <strong>{{ z.title }}</strong></label>
          </div>
          <div class="meta">{{ z.filename }} • {{ z.path }}</div>
        {% endfor %}
        <p><button type="submit">Apply selection + restart Kiwix</button></p>
      {% else %}
        <p>No ZIM files found in this folder.</p>
      {% endif %}
    </form>
  </div>

  <div class="card">
    <p><strong>Active list file:</strong> {{ list_file }}</p>
    <p class="muted">After applying, open Kiwix at: <a href="http://{{ host_ip }}:8080">http://{{ host_ip }}:8080</a></p>
    <p class="muted">Offline map UI: <a href="http://{{ host_ip }}:8091">http://{{ host_ip }}:8091</a></p>
    {% if msg %}<p><strong>{{ msg }}</strong></p>{% endif %}
  </div>
</body>
</html>
"""


def read_active():
    if not LIST_FILE.exists():
        return []
    return [line.strip() for line in LIST_FILE.read_text().splitlines() if line.strip() and not line.strip().startswith("#")]


def scan_zims(scan_dir: Path):
    if not scan_dir.exists() or not scan_dir.is_dir():
        return []
    return sorted(p for p in scan_dir.rglob("*.zim"))


def detect_icon(name: str) -> str:
    n = name.lower()
    if "wikem" in n or "med" in n:
        return "🩺"
    if "openstreetmap" in n or "map" in n or "osm" in n:
        return "🗺️"
    if "wikipedia" in n:
        return "📘"
    return "📚"


def pretty_title(name: str) -> str:
    stem = name[:-4] if name.lower().endswith(".zim") else name
    parts = [p for p in stem.replace("-", "_").split("_") if p]
    if not parts:
        return name
    skip = {"all", "maxi", "nopic", "mini", "novid", "2024", "2025", "2026"}
    words = [p for p in parts if p.lower() not in skip and not p.isdigit()]
    if not words:
        words = parts[:3]
    return " ".join(w.capitalize() for w in words[:6])


def build_profile_sets(paths):
    def match(*keys):
        keys = tuple(k.lower() for k in keys)
        return [p for p in paths if any(k in p.name.lower() for k in keys)]

    medical = match("wikem", "medical", "med")
    maps = match("openstreetmap", "osm", "map")
    general = match("wikipedia", "wikivoyage", "wiktionary")

    profiles = []
    if general:
        profiles.append({"name": "general", "label": "📘 General", "zims": general})
    if medical:
        profiles.append({"name": "medical", "label": "🩺 Medical", "zims": medical})
    if maps:
        profiles.append({"name": "maps", "label": "🗺️ Maps", "zims": maps})
    if paths:
        profiles.append({"name": "all", "label": "📚 All", "zims": paths})
    return profiles


def host_ip():
    try:
        out = subprocess.check_output(["hostname", "-I"], text=True).strip().split()
        return out[0] if out else "<PI_IP>"
    except Exception:
        return "<PI_IP>"


def restart_kiwix():
    try:
        # -n avoids hanging for password prompt in non-interactive web requests
        subprocess.check_call(["sudo", "-n", "systemctl", "restart", "kiwix.service"])
        return "Updated selection and restarted kiwix.service"
    except subprocess.CalledProcessError:
        return (
            "Saved selection, but restart failed (sudo non-interactive denied or service issue). "
            "Run ./setup_sudoers_for_zim_ui.sh once, then try again."
        )
    except Exception as e:
        return f"Saved selection, but restart failed: {e}"


@app.get("/")
def index():
    scan_dir = request.args.get("scan_dir", str(SCAN_DIR_DEFAULT))
    paths = scan_zims(Path(scan_dir))
    zims = [
        {
            "path": str(p),
            "filename": p.name,
            "title": pretty_title(p.name),
            "icon": detect_icon(p.name),
        }
        for p in paths
    ]
    profiles_raw = build_profile_sets(paths)
    profiles = [{"name": p["name"], "label": p["label"], "count": len(p["zims"])} for p in profiles_raw]

    return render_template_string(
        HTML,
        zims=zims,
        profiles=profiles,
        active=read_active(),
        scan_dir=scan_dir,
        list_file=str(LIST_FILE),
        host_ip=host_ip(),
        msg=request.args.get("msg"),
    )


@app.post("/scan")
def scan():
    scan_dir = request.form.get("scan_dir", str(SCAN_DIR_DEFAULT)).strip() or str(SCAN_DIR_DEFAULT)
    return redirect(url_for("index", scan_dir=scan_dir))


@app.post("/apply")
def apply():
    selected = request.form.getlist("selected")
    scan_dir = request.form.get("scan_dir", str(SCAN_DIR_DEFAULT))
    if not selected:
        return redirect(url_for("index", msg="Select at least one ZIM.", scan_dir=scan_dir))

    LIST_FILE.parent.mkdir(parents=True, exist_ok=True)
    LIST_FILE.write_text("\n".join(selected) + "\n")
    msg = restart_kiwix()
    return redirect(url_for("index", msg=msg, scan_dir=scan_dir))


@app.post("/apply_profile")
def apply_profile():
    scan_dir = request.form.get("scan_dir", str(SCAN_DIR_DEFAULT)).strip() or str(SCAN_DIR_DEFAULT)
    chosen = request.form.get("profile", "").strip().lower()
    paths = scan_zims(Path(scan_dir))
    profiles = {p["name"]: p["zims"] for p in build_profile_sets(paths)}

    if chosen not in profiles:
        return redirect(url_for("index", msg="Profile not found for current scan.", scan_dir=scan_dir))

    selected = [str(p) for p in profiles[chosen]]
    if not selected:
        return redirect(url_for("index", msg="That profile has no matching ZIMs.", scan_dir=scan_dir))

    LIST_FILE.parent.mkdir(parents=True, exist_ok=True)
    LIST_FILE.write_text("\n".join(selected) + "\n")
    msg = f"Applied profile '{chosen}' with {len(selected)} ZIM(s). " + restart_kiwix()
    return redirect(url_for("index", msg=msg, scan_dir=scan_dir))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8090)
