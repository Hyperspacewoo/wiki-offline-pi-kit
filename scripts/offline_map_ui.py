#!/usr/bin/env python3
from flask import Flask, send_from_directory, jsonify, request
from pathlib import Path
import json
import os

app = Flask(__name__)

RUNTIME_ROOT = Path(os.environ.get("WIKI_RUNTIME_ROOT", Path.home() / "wiki"))
MAP_ROOT = Path(os.environ.get("WIKI_MAPS_DIR", RUNTIME_ROOT / "maps"))
DATA_DIR = MAP_ROOT / "data"
STATIC_DIR = MAP_ROOT / "static"
CONFIG_FILE = MAP_ROOT / "config.json"
PLACES_FILE = DATA_DIR / "us_places.tsv"

DEFAULT_CONFIG = {
    "title": "Offgrid Intel Kit Map",
    "pmtiles": "usa.pmtiles",
    "center": [-98.58, 39.83],
    "zoom": 4,
    "minZoom": 2,
    "maxZoom": 15
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
    html, body, #map { margin:0; padding:0; width:100%; height:100%; }
    .panel { position: absolute; z-index: 3; top: 10px; left: 10px; background: rgba(255,255,255,0.96); border-radius: 10px; padding: 10px 12px; font-family: sans-serif; width: 360px; box-shadow: 0 2px 12px rgba(0,0,0,.15); }
    .small { font-size: 12px; color: #444; }
    .search { margin-top: 8px; }
    .search input, .search select { width: 100%; padding: 8px; border-radius: 8px; border: 1px solid #bbb; }
    .results { margin-top: 6px; max-height: 220px; overflow: auto; border: 1px solid #ddd; border-radius: 8px; background: #fff; }
    .result { padding: 8px; border-bottom: 1px solid #eee; cursor: pointer; }
    .result:hover { background: #f4f8ff; }
    .hidden { display: none; }
    .town-label { background: rgba(255,255,255,0.92); border: 1px solid #888; border-radius: 8px; padding: 1px 5px; font-size: 11px; font-family: sans-serif; color: #222; white-space: nowrap; }
  </style>
</head>
<body>
  <div class=\"panel\">
    <div><strong id=\"title\">Offgrid Intel Kit Map</strong></div>
    <div class=\"small\">Data: <span id=\"pmtilesName\"></span></div>
    <div class=\"search\">
      <select id=\"datasetSelect\"></select>
    </div>
    <div class=\"search\">
      <input id=\"searchInput\" placeholder=\"Search town/city (e.g., Bozeman, MT)\" />
      <div id=\"results\" class=\"results hidden\"></div>
    </div>
  </div>
  <div id=\"map\"></div>

  <script src=\"/static/maplibre-gl.js\"></script>
  <script src=\"/static/pmtiles.js\"></script>
  <script>
    let map;
    let townMarkers = [];

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

    async function boot() {
      const cfg = await fetch('/config').then(r => r.json());
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
      let timer;
      input.addEventListener('input', () => {
        clearTimeout(timer);
        const q = input.value.trim();
        if (!q || q.length < 2) { setResults([]); return; }
        timer = setTimeout(async () => {
          try {
            const items = await fetch('/search?q=' + encodeURIComponent(q)).then(r => r.json());
            setResults(items);
          } catch (_) { setResults([]); }
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
    if not PLACES_FILE.exists():
        PLACES = []
        return PLACES
    out = []
    with PLACES_FILE.open("r", encoding="utf-8", errors="ignore") as f:
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
    # Keep older configs compatible but allow deeper zoom for trail-level detail.
    try:
        data["maxZoom"] = max(15, int(data.get("maxZoom", 15)))
    except Exception:
        data["maxZoom"] = 15
    return data


def list_datasets():
    ensure_layout()
    return sorted([p.name for p in DATA_DIR.glob("*.pmtiles")])


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
    if not (DATA_DIR / pm).exists():
        return jsonify({"ok": False, "error": "dataset not found"}), 404
    cfg = load_config()
    cfg["pmtiles"] = pm
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
    return send_from_directory(DATA_DIR, name, conditional=True)


@app.get("/static/<path:name>")
def static_assets(name):
    ensure_layout()
    return send_from_directory(STATIC_DIR, name, conditional=True)


if __name__ == "__main__":
    port = int(os.environ.get("MAP_UI_PORT", "8091"))
    app.run(host="0.0.0.0", port=port)
