#!/usr/bin/env python3
from flask import Flask, send_from_directory, jsonify, request
from pathlib import Path
import json
import os

app = Flask(__name__, static_folder=None)

RUNTIME_ROOT = Path(os.environ.get("WIKI_RUNTIME_ROOT", Path.home() / "wiki"))
MAP_ROOT = Path(os.environ.get("WIKI_MAPS_DIR", RUNTIME_ROOT / "maps"))
DATA_DIR = MAP_ROOT / "data"
STATIC_DIR = MAP_ROOT / "static"
CONFIG_FILE = MAP_ROOT / "config.json"
PLACES_FILE = DATA_DIR / "us_places.tsv"
FALLBACK_PLACES_FILES = [
    Path("/home/void/.local/share/Trash/files/wiki/maps/data/us_places.tsv"),
    Path("/home/void/wiki/maps/data/us_places.tsv"),
    Path(__file__).resolve().parent.parent / "maps/data/us_places.tsv",
]
FALLBACK_STATIC_DIRS = [
    Path("/home/void/.local/share/Trash/files/wiki/maps/static"),
    Path("/home/void/wiki/maps/static"),
    Path(__file__).resolve().parent.parent / "maps/static",
]
FALLBACK_DATA_DIRS = [
    Path("/home/void/.local/share/Trash/files/wiki/maps/data"),
    Path("/home/void/wiki/maps/data"),
    Path(__file__).resolve().parent.parent / "maps/data",
]

DEFAULT_CONFIG = {
    "title": "Offgrid Intel Kit Map",
    "pmtiles": "usa.pmtiles",
    "center": [-98.58, 39.83],
    "zoom": 4,
    "minZoom": 2,
    "maxZoom": 15
}

DATASET_VIEW_HINTS = {
    "nyc.pmtiles": {"center": [-74.0, 40.72], "zoom": 9},
}

PLACES = []

INDEX_HTML = """<!doctype html>
<html>
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width,initial-scale=1\" />
  <title>Offgrid Intel Kit Map</title>
  <link rel=\"stylesheet\" href=\"/static/maplibre-gl.css\" />
  <style>
    :root {
      --panel-bg: rgba(255,255,255,0.84);
      --panel-line: rgba(211, 222, 237, 0.95);
      --panel-shadow: 0 18px 36px rgba(15, 23, 42, 0.16);
      --text: #18212f;
      --muted: #5d6a7f;
      --accent: #0a84ff;
      --accent-soft: rgba(10,132,255,0.08);
    }
    html, body, #map { margin:0; padding:0; width:100%; height:100%; }
    body {
      font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "Segoe UI", Roboto, sans-serif;
      color: var(--text);
      background: #dfe7f2;
    }
    .panel {
      position: absolute;
      z-index: 3;
      top: 16px;
      left: 16px;
      width: min(420px, calc(100vw - 32px));
      padding: 16px;
      border-radius: 20px;
      background: var(--panel-bg);
      border: 1px solid var(--panel-line);
      backdrop-filter: blur(18px);
      -webkit-backdrop-filter: blur(18px);
      box-shadow: var(--panel-shadow);
    }
    .panel-head { display:flex; align-items:flex-start; justify-content:space-between; gap:12px; }
    .traffic { display:flex; gap:6px; align-items:center; }
    .traffic i { width:10px; height:10px; border-radius:50%; display:inline-block; }
    .traffic .r { background:#ff5f57; }
    .traffic .y { background:#febc2e; }
    .traffic .g { background:#28c840; }
    .eyebrow {
      display:inline-flex;
      align-items:center;
      gap:8px;
      min-height:28px;
      padding: 6px 10px;
      border-radius:999px;
      background: var(--accent-soft);
      border: 1px solid rgba(10,132,255,0.12);
      color: #2458a6;
      font-size: 12px;
      font-weight: 600;
      margin-bottom: 10px;
    }
    .title { font-size: 20px; font-weight: 700; letter-spacing: -0.02em; margin: 0 0 4px 0; }
    .small { font-size: 12px; color: var(--muted); }
    .subtle { margin-top: 6px; line-height: 1.45; }
    .search { margin-top: 10px; }
    .search input, .search select, .panel-button {
      width: 100%;
      padding: 10px 11px;
      border-radius: 12px;
      border: 1px solid #d6deec;
      background: rgba(255,255,255,0.92);
      color: #1f2937;
      outline: none;
      box-sizing: border-box;
    }
    .search input:focus, .search select:focus {
      border-color: #7cb8ff;
      box-shadow: 0 0 0 3px rgba(10,132,255,0.14);
    }
    .results { margin-top: 6px; max-height: 220px; overflow: auto; border: 1px solid #dfe6f3; border-radius: 12px; background: rgba(255,255,255,0.96); }
    .result { padding: 10px 11px; border-bottom: 1px solid #edf1f7; cursor: pointer; }
    .result:hover { background: #f3f8ff; }
    .hidden { display: none; }
    .panel-actions {
      display:grid;
      grid-template-columns: 1fr 1fr;
      gap: 8px;
      margin-top: 10px;
    }
    .panel-button {
      text-decoration:none;
      display:inline-flex;
      align-items:center;
      justify-content:center;
      gap:8px;
      cursor:pointer;
      font-weight: 600;
      transition: background-color .14s ease, border-color .14s ease, transform .14s ease;
    }
    .panel-button:hover { background:#f3f8ff; border-color:#c7ddff; transform: translateY(-1px); }
    .panel-button.primary { background:#0a84ff; border-color:#0a84ff; color:#fff; }
    .hint {
      margin-top: 8px;
      padding: 10px 11px;
      border-radius: 12px;
      background: rgba(255,255,255,0.7);
      border: 1px solid #e3eaf5;
      color: var(--muted);
      font-size: 12px;
      line-height: 1.45;
    }
    .town-label { background: rgba(255,255,255,0.92); border: 1px solid #a7b6cc; border-radius: 8px; padding: 1px 5px; font-size: 11px; color: #1f2937; white-space: nowrap; }
    @media (max-width: 720px) {
      .panel { top: 10px; left: 10px; width: calc(100vw - 20px); padding: 14px; }
      .panel-actions { grid-template-columns: 1fr; }
    }
  </style>
</head>
<body>
  <div class="panel">
    <div class="eyebrow">Offline map workspace</div>
    <div class="panel-head">
      <div>
        <div id="title" class="title">Offgrid Intel Kit Map</div>
        <div class="small">Dataset: <span id="pmtilesName"></span></div>
      </div>
      <div class="traffic"><i class="r"></i><i class="y"></i><i class="g"></i></div>
    </div>
    <div class="small subtle">Switch local map packs, search towns offline, then jump straight back to the main dashboard when you’re done.</div>
    <div class="search">
      <select id="datasetSelect"></select>
    </div>
    <div class="search">
      <input id="searchInput" placeholder="Search town/city (e.g., Bozeman, MT)" />
      <div id="results" class="results hidden"></div>
      <div id="searchHint" class="hint">Search uses the local places index and gets more useful as you zoom in.</div>
    </div>
    <div class="panel-actions">
      <button class="panel-button primary" type="button" onclick="resetView()">Reset view</button>
      <a class="panel-button" href="/">Back to dashboard</a>
    </div>
  </div>
  <div id="map"></div>

  <script src=\"/static/maplibre-gl.js\"></script>
  <script src=\"/static/pmtiles.js\"></script>
  <script>
    let map;
    let townMarkers = [];
    let initialView = { center: [-98.58, 39.83], zoom: 4 };

    function clearTownMarkers() {
      townMarkers.forEach(m => m.remove());
      townMarkers = [];
    }

    function addTownLabel(t) {
      const el = document.createElement('div');
      el.className = 'town-label';
      el.textContent = t.name;
      const m = new maplibregl.Marker({ element: el, anchor: 'center' })
        .setLngLat([t.lon, t.lat])
        .addTo(map);
      townMarkers.push(m);
    }

    async function refreshTownLabels() {
      if (!map) return;
      const z = map.getZoom();
      if (z < 6) { clearTownMarkers(); return; }
      const b = map.getBounds();
      const q = new URLSearchParams({
        minLon: b.getWest(), minLat: b.getSouth(), maxLon: b.getEast(), maxLat: b.getNorth(), zoom: z
      });
      try {
        const towns = await fetch('/towns?' + q.toString()).then(r => r.json());
        clearTownMarkers();
        towns.forEach(addTownLabel);
      } catch (_) {}
    }

    function setResults(items) {
      const box = document.getElementById('results');
      box.innerHTML = '';
      if (!items.length) {
        box.classList.add('hidden');
        return;
      }
      items.forEach(it => {
        const d = document.createElement('div');
        d.className = 'result';
        d.textContent = `${it.name}${it.admin1 ? ', ' + it.admin1 : ''} (pop ${it.population || 0})`;
        d.onclick = () => {
          map.flyTo({ center: [it.lon, it.lat], zoom: 13 });
          box.classList.add('hidden');
          const p = new maplibregl.Popup({ closeOnClick: true })
            .setLngLat([it.lon, it.lat])
            .setHTML(`<b>${it.name}</b>${it.admin1 ? ', ' + it.admin1 : ''}<br/>Population: ${it.population || 0}`)
            .addTo(map);
          setTimeout(() => p.remove(), 7000);
        };
        box.appendChild(d);
      });
      box.classList.remove('hidden');
    }

    function resetView() {
      if (!map) return;
      map.flyTo({ center: initialView.center, zoom: initialView.zoom });
    }

    async function boot() {
      const cfg = await fetch('/config').then(r => r.json());
      initialView = {
        center: cfg.center || [-98.58, 39.83],
        zoom: cfg.zoom || 4
      };
      document.getElementById('title').textContent = cfg.title || 'Offgrid Intel Kit Map';
      document.getElementById('pmtilesName').textContent = cfg.pmtiles;

      try {
        const datasets = await fetch('/datasets').then(r => r.json());
        const sel = document.getElementById('datasetSelect');
        sel.innerHTML = datasets.map(d => `<option value="${d}" ${d===cfg.pmtiles?'selected':''}>Map: ${d}</option>`).join('');
        sel.onchange = async () => {
          const name = sel.value;
          await fetch('/set_dataset', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({pmtiles:name})});
          location.reload();
        };
      } catch (_) {}

      const protocol = new pmtiles.Protocol();
      maplibregl.addProtocol('pmtiles', protocol.tile);

      map = new maplibregl.Map({
        container: 'map',
        style: {
          version: 8,
          sources: {
            protomaps: {
              type: 'vector',
              url: `pmtiles://${location.origin}/tiles/${cfg.pmtiles}`
            }
          },
          layers: [
            { id: 'bg', type: 'background', paint: { 'background-color': '#f2efe9' } },
            { id: 'water', type: 'fill', source: 'protomaps', 'source-layer': 'water', paint: {'fill-color': '#9ecae1'} },
            { id: 'landuse', type: 'fill', source: 'protomaps', 'source-layer': 'landuse', paint: {'fill-color': '#d9eac8', 'fill-opacity': 0.5} },
            { id: 'roads', type: 'line', source: 'protomaps', 'source-layer': 'roads', paint: {'line-color': '#ffffff', 'line-width': ['interpolate', ['linear'], ['zoom'], 4, 0.3, 10, 2, 13, 3.2, 15, 4.4]} },
            {
              id: 'trails',
              type: 'line',
              source: 'protomaps',
              'source-layer': 'roads',
              filter: ['any', ['==', ['get', 'class'], 'path'], ['==', ['get', 'kind'], 'path']],
              paint: {
                'line-color': '#9a6b3f',
                'line-width': ['interpolate', ['linear'], ['zoom'], 10, 0.5, 12, 1.2, 14, 2.3, 15, 3],
                'line-dasharray': [1.2, 1.2],
                'line-opacity': 0.9
              }
            },
            { id: 'boundaries', type: 'line', source: 'protomaps', 'source-layer': 'boundaries', paint: {'line-color': '#888', 'line-dasharray': [2,2], 'line-width': 1} }
          ]
        },
        center: cfg.center || [-98.58, 39.83],
        zoom: cfg.zoom || 4,
        minZoom: cfg.minZoom || 2,
        maxZoom: cfg.maxZoom || 15,
        hash: true
      });

      map.addControl(new maplibregl.NavigationControl(), 'top-right');
      map.on('load', refreshTownLabels);
      map.on('moveend', refreshTownLabels);

      const input = document.getElementById('searchInput');
      const hint = document.getElementById('searchHint');
      let timer;
      input.addEventListener('input', () => {
        clearTimeout(timer);
        const q = input.value.trim();
        if (!q || q.length < 2) { setResults([]); if (hint) hint.textContent = 'Offline place search depends on the local places index.'; return; }
        timer = setTimeout(async () => {
          try {
            const items = await fetch('/search?q=' + encodeURIComponent(q)).then(r => r.json());
            setResults(items);
            if (hint) hint.textContent = items.length ? `Found ${items.length} result${items.length === 1 ? '' : 's'}.` : 'No local place index matches. The map dataset still works.';
          } catch (_) { setResults([]); if (hint) hint.textContent = 'Search unavailable right now.'; }
        }, 150);
      });
    }
    boot();
  </script>
</body>
</html>"""


def ensure_layout():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    STATIC_DIR.mkdir(parents=True, exist_ok=True)
    if not CONFIG_FILE.exists():
        CONFIG_FILE.write_text(json.dumps(DEFAULT_CONFIG, indent=2) + "\n")


def load_places():
    global PLACES
    if PLACES:
        return PLACES
    place_file = PLACES_FILE if PLACES_FILE.exists() else None
    if place_file is None:
        for cand in FALLBACK_PLACES_FILES:
            if cand.exists():
                place_file = cand
                break
    if place_file is None:
        PLACES = []
        return PLACES
    out = []
    with place_file.open("r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split("\t")
            if len(parts) != 5:
                continue
            name, admin1, lat, lon, pop = parts
            try:
                out.append({
                    "name": name,
                    "admin1": admin1,
                    "lat": float(lat),
                    "lon": float(lon),
                    "population": int(pop),
                })
            except Exception:
                continue
    PLACES = out
    return PLACES


def load_config():
    ensure_layout()
    try:
        data = json.loads(CONFIG_FILE.read_text())
    except Exception:
        data = dict(DEFAULT_CONFIG)
    for k, v in DEFAULT_CONFIG.items():
        data.setdefault(k, v)
    datasets = list_datasets()
    preferred = "usa.pmtiles" if "usa.pmtiles" in datasets else (datasets[0] if datasets else data.get("pmtiles", DEFAULT_CONFIG["pmtiles"]))
    if not data.get("pmtiles") or data.get("pmtiles") not in datasets:
        data["pmtiles"] = preferred

    # Helpful first-view defaults for starter extracts.
    hint = DATASET_VIEW_HINTS.get(str(data.get("pmtiles", "")).lower())
    if hint:
        center = data.get("center")
        zoom = data.get("zoom")
        if center == DEFAULT_CONFIG["center"] or center is None:
            data["center"] = hint["center"]
        if zoom == DEFAULT_CONFIG["zoom"] or zoom is None:
            data["zoom"] = hint["zoom"]
    # Keep older configs compatible but allow deeper zoom for trail-level detail.
    try:
        data["maxZoom"] = max(15, int(data.get("maxZoom", 15)))
    except Exception:
        data["maxZoom"] = 15
    return data


def list_datasets():
    ensure_layout()
    names = {p.name for p in DATA_DIR.glob("*.pmtiles")}
    for d in FALLBACK_DATA_DIRS:
        if d.exists():
            names.update(p.name for p in d.glob("*.pmtiles"))
    return sorted(names)


@app.get("/")
def index():
    ensure_layout()
    return INDEX_HTML


@app.get("/config")
def config():
    return jsonify(load_config())


@app.get("/datasets")
def datasets():
    return jsonify(list_datasets())


@app.post("/set_dataset")
def set_dataset():
    payload = request.get_json(silent=True) or {}
    pm = (payload.get("pmtiles") or "").strip()
    if not pm or "/" in pm or ".." in pm or not pm.endswith('.pmtiles'):
        return jsonify({"ok": False, "error": "invalid dataset"}), 400
    exists = (DATA_DIR / pm).exists() or any((d / pm).exists() for d in FALLBACK_DATA_DIRS if d.exists())
    if not exists:
        return jsonify({"ok": False, "error": "dataset not found"}), 404
    cfg = load_config()
    cfg["pmtiles"] = pm
    hint = DATASET_VIEW_HINTS.get(pm.lower())
    if hint and (cfg.get("center") == DEFAULT_CONFIG["center"] or cfg.get("center") is None):
        cfg["center"] = hint["center"]
    if hint and (cfg.get("zoom") == DEFAULT_CONFIG["zoom"] or cfg.get("zoom") is None):
        cfg["zoom"] = hint["zoom"]
    CONFIG_FILE.write_text(json.dumps(cfg, indent=2) + "\n")
    return jsonify({"ok": True, "pmtiles": pm})


@app.get("/search")
def search():
    q = (request.args.get("q") or "").strip().lower()
    if len(q) < 2:
        return jsonify([])
    places = load_places()
    hits = []
    for p in places:
        target = f"{p['name']} {p['admin1']}".lower()
        if q in target:
            hits.append(p)
        if len(hits) >= 20:
            break
    hits.sort(key=lambda x: x.get("population", 0), reverse=True)
    return jsonify(hits[:12])


@app.get("/towns")
def towns():
    places = load_places()
    try:
        min_lon = float(request.args.get("minLon"))
        min_lat = float(request.args.get("minLat"))
        max_lon = float(request.args.get("maxLon"))
        max_lat = float(request.args.get("maxLat"))
        zoom = float(request.args.get("zoom", 0))
    except Exception:
        return jsonify([])

    if zoom >= 9:
        min_pop = 5000
    elif zoom >= 8:
        min_pop = 15000
    elif zoom >= 7:
        min_pop = 40000
    else:
        min_pop = 80000

    out = []
    for p in places:
        if p["population"] < min_pop:
            continue
        if min_lon <= p["lon"] <= max_lon and min_lat <= p["lat"] <= max_lat:
            out.append(p)
    out.sort(key=lambda x: x["population"], reverse=True)
    return jsonify(out[:120])


@app.get("/tiles/<path:name>")
def tiles(name):
    ensure_layout()
    target = DATA_DIR / name
    if target.exists():
        return send_from_directory(DATA_DIR, name, conditional=True)
    for d in FALLBACK_DATA_DIRS:
        candidate = d / name
        if candidate.exists():
            return send_from_directory(d, name, conditional=True)
    return ("Not found", 404)


@app.get("/static/<path:name>")
def static_assets(name):
    ensure_layout()
    target = STATIC_DIR / name
    if target.exists():
        return send_from_directory(STATIC_DIR, name, conditional=True)
    for d in FALLBACK_STATIC_DIRS:
        candidate = d / name
        if candidate.exists():
            return send_from_directory(d, name, conditional=True)
    return ("Not found", 404)


if __name__ == "__main__":
    port = int(os.environ.get("MAP_UI_PORT", "8091"))
    app.run(host="0.0.0.0", port=port)
