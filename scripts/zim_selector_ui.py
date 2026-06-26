#!/usr/bin/env python3
from flask import Flask, Response, request, render_template_string, jsonify, send_file, abort, redirect
from pathlib import Path
import subprocess
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote, urlencode
import shlex
import os
import json
import re
import time

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
VERSION_FILE = KIT_ROOT / "config" / "VERSION.json"
LOCAL_UPDATE_MANIFEST_FILE = KIT_ROOT / "config" / "update_manifest.json"
DEFAULT_UPDATE_MANIFEST_URL = "https://raw.githubusercontent.com/Hyperspacewoo/wiki-offline-pi-kit/main/config/update_manifest.json"

HTML = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Offgrid Kit • Offline Console</title>
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

    function rescan() {
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
        if (out) out.textContent = (data.ok ? '✅ ' : '⚠️ ') + (data.message || '') + (data.output ? '\\n\\n' + data.output : '');
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
          <div class="search-item">
            <div class="search-title">${i+1}. ${r.title}</div>
            <div class="muted small"><a href="${r.url}" target="_blank">Open full article</a></div>
            <button class="btn btn-soft" onclick="wikiParse('${encodeURIComponent(r.url)}')">Parse excerpt</button>
          </div>
        `).join('');
      } catch (e) { list.innerHTML = '<div class="muted">Search failed.</div>'; }
    }
    function useParsedForAI() {
      const parsed = document.getElementById('wikiParsed');
      const ctx = document.getElementById('aiContext');
      if (parsed && ctx) {
        ctx.value = parsed.textContent || '';
      }
    }

    async function wikiParse(url) {
      const parsed = document.getElementById('wikiParsed');
      parsed.textContent = 'Parsing…';
      try {
        const data = await fetch('/api/wiki/parse?url=' + encodeURIComponent(url)).then(r => r.json());
        parsed.textContent = data.text || 'No text extracted.';
      } catch (e) { parsed.textContent = 'Parse failed.'; }
    }

    function swapTranslatorLangs() {
      const src = document.getElementById('trSource');
      const dst = document.getElementById('trTarget');
      const t = src.value;
      src.value = dst.value;
      dst.value = t;
    }

    function applyTheme(theme) {
      const safeTheme = theme === 'dark' ? 'dark' : 'light';
      document.documentElement.setAttribute('data-theme', safeTheme);
      const toggle = document.getElementById('themeToggle');
      if (toggle) toggle.textContent = safeTheme === 'dark' ? '☀️ Light' : '🌙 Dark';
    }

    function toggleTheme() {
      const current = document.documentElement.getAttribute('data-theme') === 'dark' ? 'dark' : 'light';
      const next = current === 'dark' ? 'light' : 'dark';
      localStorage.setItem('wikiTheme', next);
      applyTheme(next);
    }

    function fillMiniAiPrompt(text) {
      const prompt = document.getElementById('miniAiPrompt');
      if (!prompt) return;
      prompt.value = text;
      prompt.focus();
    }

    document.addEventListener('DOMContentLoaded', () => {
      applyTheme(localStorage.getItem('wikiTheme') || 'light');
      applyFilters();
      sortRows();
      const filterInput = document.getElementById('q');
      document.addEventListener('keydown', (e) => {
        if (e.key === '/' && document.activeElement !== filterInput) {
          e.preventDefault();
          filterInput.focus();
        }
      });
      initMiniAiWidget();
    });

    function mergeStreamChunk(existing, chunk) {
      if (!existing) return chunk;
      if (!chunk) return existing;
      const last = existing.slice(-1);
      const first = chunk.slice(0, 1);
      const needsSpace = /[A-Za-z0-9]/.test(last) && /[A-Za-z0-9]/.test(first);
      return existing + (needsSpace ? ' ' : '') + chunk;
    }

    function initMiniAiWidget() {
      const prompt = document.getElementById('miniAiPrompt');
      const send = document.getElementById('miniAiSend');
      const output = document.getElementById('miniAiOutput');
      const spinner = document.getElementById('miniAiSpinner');
      const modelSel = document.getElementById('miniAiModel');
      const modelSwitch = document.getElementById('miniAiSwitch');
      const modelStatus = document.getElementById('miniAiModelStatus');
      if (!prompt || !send || !output) return;

      async function switchModel() {
        if (!modelSel) return;
        const chosen = (modelSel.value || '').trim();
        if (!chosen) return;
        if (modelStatus) modelStatus.textContent = 'Switching model...';
        try {
          const r = await fetch('/api/ai/model/select', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ model: chosen })
          });
          const data = await r.json();
          if (!r.ok || !data.ok) throw new Error(data.error || 'Switch failed');
          if (modelStatus) modelStatus.textContent = '✅ ' + (data.message || 'Model switched');
          const aiLabel = document.getElementById('aiStatusLabel');
          const aiDetail = document.getElementById('aiStatusDetail');
          if (data.status) {
            if (aiLabel) aiLabel.textContent = data.status.label || 'AI online';
            if (aiDetail) aiDetail.textContent = data.status.detail || '';
          }
        } catch (e) {
          if (modelStatus) modelStatus.textContent = '⚠️ ' + e.message;
        }
      }

      async function run() {
        const value = (prompt.value || '').trim();
        if (!value) return;
        if (output.textContent.includes('Offline AI ready.')) output.innerHTML = '';
        const userBubble = document.createElement('div');
        userBubble.className = 'chat-bubble user';
        userBubble.textContent = value;
        output.appendChild(userBubble);
        prompt.value = '';
        output.scrollTop = output.scrollHeight;
        if (spinner) spinner.style.display = 'inline-flex';
        const assistantBubble = document.createElement('div');
        assistantBubble.className = 'chat-bubble assistant';
        assistantBubble.textContent = '';
        output.appendChild(assistantBubble);
        output.scrollTop = output.scrollHeight;
        try {
          const r = await fetch('/api/ai/stream', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ prompt: value, context: '', model_choice: (modelSel ? modelSel.value : '') })
          });
          if (!r.ok || !r.body) {
            assistantBubble.textContent = 'Offline AI request failed.';
          } else {
            const reader = r.body.getReader();
            const decoder = new TextDecoder();
            while (true) {
              const { value: chunkValue, done } = await reader.read();
              if (done) break;
              const chunk = decoder.decode(chunkValue, { stream: true });
              assistantBubble.textContent += chunk;
              output.scrollTop = output.scrollHeight;
            }
            if (!assistantBubble.textContent.trim()) {
              assistantBubble.textContent = 'No output returned.';
            }
          }
        } catch (e) {
          assistantBubble.textContent = 'Offline AI request failed.';
        } finally {
          if (spinner) spinner.style.display = 'none';
        }
      }

      send.addEventListener('click', run);
      if (modelSwitch) modelSwitch.addEventListener('click', switchModel);
      prompt.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
          e.preventDefault();
          run();
        }
      });
    }

</script>
  <style>
    :root {
      --bg: #f4f6fb;
      --surface: rgba(255, 255, 255, 0.78);
      --surface-2: #ffffff;
      --line: #dbe2ef;
      --text: #1f2937;
      --muted: #6b7280;
      --primary: #0a84ff;
      --accent: #5ac8fa;
      --warning: #f59e0b;
      --ok: #34c759;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      color: var(--text);
      font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "Segoe UI", Roboto, sans-serif;
      background:
        radial-gradient(circle at top left, rgba(90, 200, 250, 0.18), transparent 28%),
        radial-gradient(circle at top right, rgba(10, 132, 255, 0.16), transparent 24%),
        linear-gradient(180deg, #f8fbff 0%, #ecf2fb 52%, #e7eef9 100%);
    }
    a { color: inherit; text-decoration: none; }
    button, input, select, textarea { font: inherit; }
    h1, h2, h3, p { margin: 0; }

    .shell {
      max-width: 1440px;
      margin: 0 auto;
      padding: 26px;
    }
    .glass {
      background: var(--surface);
      border: 1px solid var(--line);
      border-radius: 22px;
      backdrop-filter: blur(18px);
      -webkit-backdrop-filter: blur(18px);
      box-shadow: 0 18px 44px rgba(15, 23, 42, 0.09);
    }
    .section { padding: 22px; margin-bottom: 14px; }
    .hero-top { display: block; }
    .eyebrow { display: none; }
    .hero-title { font-size: 30px; font-weight: 700; margin-bottom: 6px; letter-spacing: -0.02em; }
    .hero-copy { color: var(--muted); margin-bottom: 14px; line-height: 1.5; }
    .hero-actions, .action-row, .quick-grid, .button-row { display: flex; gap: 8px; flex-wrap: wrap; }
    .status-card, .status-head { display: block; }
    .tiny { display: none; }
    .status-pill {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 6px 10px;
      border-radius: 999px;
      border: 1px solid var(--line);
      font-size: 12px;
      color: var(--muted);
      background: #f8fbff;
    }
    .dot { width: 8px; height: 8px; border-radius: 50%; background: var(--ok); }
    .dot.warn { background: var(--warning); }

    .stats-grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 10px; margin-top: 12px; }
    .stat-card { padding: 14px; border-radius: 12px; background: var(--surface-2); border: 1px solid var(--line); }
    .stat-label { color: var(--muted); font-size: 12px; }
    .stat-value { font-size: 24px; font-weight: 600; margin-top: 6px; }

    .btn {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 6px;
      min-height: 40px;
      padding: 9px 12px;
      border-radius: 10px;
      border: 1px solid var(--line);
      background: #ffffff;
      color: var(--text);
      cursor: pointer;
      transition: background-color .15s ease, border-color .15s ease, box-shadow .15s ease;
    }
    .btn:hover { background: #f6f9ff; border-color: #cfd8e8; }
    .btn:focus-visible { outline: none; box-shadow: 0 0 0 3px rgba(10,132,255,0.18); }
    .btn-accent { background: #0a84ff; border-color: #0a84ff; color: #ffffff; }
    .btn-accent:hover { background: #0078f0; border-color: #0078f0; }
    .btn-mint { background: #e8f7ff; border-color: #c5e8ff; color: #0b5c8e; }
    .btn-soft { background: #ffffff; }

    .input, .select, .textarea {
      width: 100%;
      border-radius: 10px;
      border: 1px solid var(--line);
      background: #ffffff;
      color: var(--text);
      padding: 10px 12px;
      outline: none;
    }
    .input::placeholder, .textarea::placeholder { color: #9aa3b2; }
    .input:focus, .select:focus, .textarea:focus { border-color: #7bb8ff; box-shadow: 0 0 0 3px rgba(10,132,255,0.14); }
    .textarea { min-height: 110px; resize: vertical; }

    .toolbar { display: grid; grid-template-columns: 1fr auto auto; gap: 10px; align-items: center; }
    .chips { display: flex; gap: 8px; flex-wrap: wrap; align-items: center; margin-top: 12px; }
    .chip {
      padding: 7px 10px;
      border-radius: 999px;
      border: 1px solid var(--line);
      background: #ffffff;
      color: var(--muted);
      cursor: pointer;
    }
    .chip.active, .chip:hover { background: #eef5ff; color: #2458a6; border-color: #c7ddff; }
    .visible-count { font-size: 12px; color: var(--muted); }

    .layout { display: grid; grid-template-columns: 1.7fr 1fr; gap: 12px; }
    .table-wrap { margin-top: 12px; overflow: auto; border-radius: 12px; border: 1px solid var(--line); background: #ffffff; max-height: 58vh; }
    table { width: 100%; min-width: 900px; border-collapse: collapse; }
    th, td { padding: 12px; border-top: 1px solid #edf1f7; text-align: left; vertical-align: top; }
    th {
      position: sticky;
      top: 0;
      z-index: 1;
      background: #f8fbff;
      border-top: none;
      color: var(--muted);
      font-size: 12px;
      font-weight: 600;
    }
    tbody tr:hover { background: #f8fbff; }
    .file-name { font-size: 12px; color: var(--muted); margin-top: 4px; }
    .badge {
      display: inline-block;
      padding: 4px 8px;
      border-radius: 8px;
      border: 1px solid var(--line);
      background: #f8fbff;
      font-size: 12px;
      color: var(--muted);
    }
    .path { font-size: 12px; color: var(--muted); word-break: break-all; }

    .side-stack { display: grid; gap: 12px; }
    .quick-grid { display: grid; gap: 8px; }
    .subcopy { margin-top: 8px; color: var(--muted); font-size: 13px; }
    .split { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-top: 12px; }
    .panel-box {
      border-radius: 12px;
      border: 1px solid var(--line);
      background: #ffffff;
      padding: 12px;
      max-height: 300px;
      overflow: auto;
    }
    .search-item { padding: 10px 0; border-bottom: 1px solid #edf1f7; }
    .search-item:last-child { border-bottom: none; }
    .search-title { font-weight: 600; }
    .small { font-size: 12px; }
    .muted { color: var(--muted); }
    .translator-row { display: grid; grid-template-columns: 1fr auto 1fr; gap: 8px; align-items: center; }

    .pre {
      margin-top: 12px;
      padding: 12px;
      border-radius: 10px;
      border: 1px solid var(--line);
      background: #ffffff;
      color: var(--text);
      white-space: pre-wrap;
      overflow: auto;
      font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
      font-size: 12px;
      line-height: 1.45;
    }

    .chat-shell { border-radius: 12px; border: 1px solid var(--line); background: #ffffff; padding: 12px; margin-top: 12px; }
    .chat-output { min-height: 220px; max-height: 48vh; overflow: auto; display:flex; flex-direction:column; gap:10px; }
    .chat-bubble { max-width: 92%; border-radius: 12px; padding: 10px 12px; white-space: pre-wrap; line-height: 1.6; }
    .chat-bubble.user { align-self: flex-end; background: #0a84ff; border: 1px solid #0a84ff; color: #ffffff; }
    .chat-bubble.assistant { align-self: flex-start; background: #f7f9fc; border: 1px solid #dde6f2; color: var(--text); }
    .chat-spinner { display:none; align-items:center; gap:8px; color: var(--muted); font-size: 13px; margin-top: 8px; }
    .spinner-dot { width: 8px; height: 8px; border-radius: 50%; background: var(--accent); animation: pulse 1s infinite ease-in-out; }
    .spinner-dot:nth-child(2) { animation-delay: .15s; }
    .spinner-dot:nth-child(3) { animation-delay: .3s; }
    @keyframes pulse { 0%, 80%, 100% { opacity: .35; } 40% { opacity: 1; } }

    .hero-grid {
      display: grid;
      grid-template-columns: minmax(0, 1.7fr) minmax(320px, 0.95fr);
      gap: 16px;
      align-items: stretch;
    }
    .hero-card {
      padding: 24px;
      border-radius: 20px;
      background:
        radial-gradient(circle at 16% 18%, rgba(255,255,255,0.8), transparent 20%),
        radial-gradient(circle at top right, rgba(90, 200, 250, 0.28), transparent 28%),
        radial-gradient(circle at bottom left, rgba(10,132,255,0.12), transparent 30%),
        linear-gradient(135deg, rgba(255,255,255,0.98) 0%, rgba(244,249,255,0.95) 58%, rgba(236,244,255,0.96) 100%);
      border: 1px solid rgba(219, 226, 239, 0.96);
      box-shadow: 0 24px 56px rgba(15, 23, 42, 0.12);
    }
    .eyebrow {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 7px 11px;
      border-radius: 999px;
      background: rgba(10,132,255,0.08);
      border: 1px solid rgba(10,132,255,0.12);
      color: #2458a6;
      font-size: 12px;
      font-weight: 700;
      letter-spacing: 0.02em;
      margin-bottom: 14px;
      box-shadow: inset 0 1px 0 rgba(255,255,255,0.55);
    }
    .hero-title { font-size: 44px; line-height: 0.98; margin-bottom: 12px; letter-spacing: -0.035em; }
    .hero-copy { font-size: 16px; max-width: 58ch; margin-bottom: 18px; line-height: 1.55; }
    .meta-row {
      display: flex;
      gap: 10px;
      flex-wrap: wrap;
      margin: 14px 0 18px;
    }
    .meta-pill {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      min-height: 36px;
      padding: 8px 12px;
      border-radius: 999px;
      background: rgba(255,255,255,0.82);
      border: 1px solid rgba(219, 226, 239, 0.9);
      color: #475569;
      font-size: 13px;
    }
    .meta-pill strong { color: var(--text); }
    .hero-actions { margin-bottom: 10px; }
    .hero-actions .btn { min-height: 44px; padding: 11px 14px; }
    .hero-note {
      margin-top: 12px;
      padding: 12px 14px;
      border-radius: 14px;
      background: rgba(255,255,255,0.72);
      border: 1px solid rgba(219,226,239,0.9);
      color: #526076;
      font-size: 13px;
      line-height: 1.5;
    }
    .trust-strip {
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 10px;
      margin-top: 16px;
    }
    .trust-card {
      min-height: 78px;
      border: 1px solid rgba(219,226,239,0.92);
      border-radius: 16px;
      background: rgba(255,255,255,0.78);
      padding: 12px;
      color: #526076;
      font-size: 13px;
      line-height: 1.35;
    }
    .trust-card strong {
      display: block;
      color: var(--text);
      margin-bottom: 4px;
      font-size: 14px;
    }
    .system-rail {
      display: grid;
      gap: 12px;
      padding: 18px;
      border-radius: 18px;
      background:
        radial-gradient(circle at top right, rgba(122, 211, 252, 0.16), transparent 26%),
        linear-gradient(180deg, rgba(255,255,255,0.96), rgba(248,251,255,0.9));
      border: 1px solid rgba(219, 226, 239, 0.95);
      box-shadow: inset 0 1px 0 rgba(255,255,255,0.65), 0 14px 32px rgba(15, 23, 42, 0.05);
    }
    .system-head {
      display:flex;
      justify-content:space-between;
      gap:12px;
      align-items:flex-start;
      flex-wrap:wrap;
    }
    .system-list { display:grid; gap:10px; }
    .system-item {
      padding: 12px 14px;
      border-radius: 14px;
      border: 1px solid #e5ebf5;
      background: rgba(255,255,255,0.88);
    }
    .system-item label {
      display:block;
      font-size: 12px;
      color: var(--muted);
      margin-bottom: 4px;
    }
    .system-item strong { display:block; font-size: 14px; }
    .launch-grid {
      display:grid;
      grid-template-columns: repeat(auto-fit, minmax(190px, 1fr));
      gap: 14px;
      margin-bottom: 18px;
    }
    .launch-card {
      display:block;
      position: relative;
      overflow: hidden;
      padding: 18px;
      border-radius: 20px;
      background: linear-gradient(180deg, rgba(255,255,255,0.98), rgba(247,250,255,0.94));
      border: 1px solid rgba(219,226,239,0.96);
      box-shadow: 0 14px 34px rgba(30, 41, 59, 0.08);
      transition: transform .16s ease, box-shadow .16s ease, border-color .16s ease;
    }
    .launch-card:hover {
      transform: translateY(-3px);
      border-color: #bcd9ff;
      box-shadow: 0 20px 38px rgba(10,132,255,0.12);
    }
    .launch-kicker {
      font-size: 12px;
      color: #2458a6;
      font-weight: 600;
      margin-bottom: 8px;
    }
    .launch-title { font-size: 16px; font-weight: 700; margin-bottom: 6px; }
    .launch-copy { font-size: 13px; color: var(--muted); line-height: 1.45; }
    .section-head {
      display:flex;
      justify-content:space-between;
      gap:16px;
      align-items:flex-start;
      flex-wrap:wrap;
      margin-bottom: 14px;
    }
    .section-head h2 { margin-bottom: 4px; }
    .theme-toggle { min-height: 36px; padding: 8px 12px; }
    .launch-card::after {
      content: '↗';
      position: absolute;
      top: 16px;
      right: 16px;
      width: 32px;
      height: 32px;
      border-radius: 999px;
      display: grid;
      place-items: center;
      background: rgba(255,255,255,0.72);
      border: 1px solid rgba(255,255,255,0.8);
      color: #174a89;
      font-weight: 700;
      box-shadow: 0 10px 22px rgba(15, 23, 42, 0.08);
    }
    .card-knowledge { background: linear-gradient(180deg, #fdfefe, #eef8ff 100%); }
    .card-maps { background: linear-gradient(180deg, #fbfffd, #eefbf4 100%); }
    .card-library { background: linear-gradient(180deg, #fffefd, #fff6eb 100%); }
    .card-help { background: linear-gradient(180deg, #fffefe, #f7f0ff 100%); }
    .scenario-grid {
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 10px;
      margin: 14px 0 18px;
    }
    .scenario-card {
      border: 1px solid rgba(219,226,239,0.96);
      border-radius: 16px;
      background: rgba(255,255,255,0.86);
      padding: 13px 14px;
      min-height: 96px;
      box-shadow: 0 10px 24px rgba(30, 41, 59, 0.06);
      transition: transform .16s ease, border-color .16s ease;
    }
    .scenario-card:hover { transform: translateY(-2px); border-color: #bcd9ff; }
    .scenario-card strong { display:block; margin-bottom:6px; }
    .scenario-card span { color: var(--muted); font-size: 13px; line-height: 1.4; }
    .feature { position: relative; overflow: hidden; }
    .feature::before {
      content: '';
      position: absolute;
      inset: 0;
      pointer-events: none;
      background: radial-gradient(circle at top right, rgba(255,255,255,0.45), transparent 26%);
    }
    .feature > * { position: relative; z-index: 1; }
    .feature-ai { background: linear-gradient(180deg, rgba(242,248,255,0.9), rgba(255,255,255,0.82)); }
    .feature-library { background: linear-gradient(180deg, rgba(250,252,255,0.92), rgba(255,255,255,0.84)); }
    .feature-search { background: linear-gradient(180deg, rgba(245,251,255,0.9), rgba(255,255,255,0.84)); }
    .feature-emergency { background: linear-gradient(180deg, rgba(255,249,240,0.92), rgba(255,255,255,0.85)); }
    .feature-translate { background: linear-gradient(180deg, rgba(242,255,251,0.92), rgba(255,255,255,0.85)); }
    .suggestion-row { display:flex; gap:8px; flex-wrap:wrap; margin-top:12px; }
    .prompt-chip { background: rgba(255,255,255,0.82); }
    .soft-note {
      margin-top: 10px;
      padding: 10px 12px;
      border-radius: 12px;
      border: 1px solid rgba(219, 226, 239, 0.9);
      background: rgba(255,255,255,0.72);
      color: var(--muted);
      font-size: 13px;
      line-height: 1.45;
    }

    [data-theme="dark"] {
      --bg: #08111f;
      --surface: rgba(11, 19, 34, 0.82);
      --surface-2: #0f1a2d;
      --line: #22324b;
      --text: #ecf3ff;
      --muted: #9eb1cc;
      --primary: #6cb6ff;
      --accent: #7dd3fc;
      --warning: #f7b955;
      --ok: #40d38a;
    }
    [data-theme="dark"] body { background: linear-gradient(180deg, #08111f 0%, #0d1727 100%); }
    [data-theme="dark"] .glass,
    [data-theme="dark"] .hero-card,
    [data-theme="dark"] .system-rail,
    [data-theme="dark"] .launch-card,
    [data-theme="dark"] .stat-card,
    [data-theme="dark"] .panel-box,
    [data-theme="dark"] .chat-shell,
    [data-theme="dark"] .hero-note,
    [data-theme="dark"] .meta-pill,
    [data-theme="dark"] .system-item,
    [data-theme="dark"] .trust-card,
    [data-theme="dark"] .scenario-card,
    [data-theme="dark"] .results-box,
    [data-theme="dark"] .pre {
      background: #0f1a2d;
      border-color: #22324b;
      color: #ecf3ff;
      box-shadow: none;
    }
    [data-theme="dark"] .launch-card:hover { box-shadow: 0 18px 34px rgba(0,0,0,0.34); }
    [data-theme="dark"] .card-knowledge,
    [data-theme="dark"] .card-maps,
    [data-theme="dark"] .card-library,
    [data-theme="dark"] .card-help,
    [data-theme="dark"] .feature-ai,
    [data-theme="dark"] .feature-library,
    [data-theme="dark"] .feature-search,
    [data-theme="dark"] .feature-emergency,
    [data-theme="dark"] .feature-translate { background: #0f1a2d; }
    [data-theme="dark"] .launch-card::after,
    [data-theme="dark"] .soft-note { background: #13233c; border-color: #263754; color: #d9e8ff; }
    [data-theme="dark"] .input,
    [data-theme="dark"] .select,
    [data-theme="dark"] .textarea,
    [data-theme="dark"] .btn,
    [data-theme="dark"] .chip,
    [data-theme="dark"] th,
    [data-theme="dark"] tbody tr:hover,
    [data-theme="dark"] .badge {
      background: #13233c;
      border-color: #263754;
      color: #d9e8ff;
    }
    [data-theme="dark"] .btn-accent { background: #6cb6ff; border-color: #6cb6ff; color: #04101e; }
    [data-theme="dark"] .btn-mint { background: #0f2940; border-color: #234768; color: #bde8ff; }
    [data-theme="dark"] .chip.active, [data-theme="dark"] .chip:hover { background: #18304f; color: #d9e8ff; border-color: #2d4f76; }
    [data-theme="dark"] .chat-bubble.assistant { background: #13233c; border-color: #263754; color: #ecf3ff; }
    [data-theme="dark"] table { background: #0f1a2d; }

    details summary { cursor: pointer; font-weight: 600; }
    .reveal, .reveal.show { opacity: 1; transform: none; }

    @media (max-width: 1100px) {
      .hero-grid, .layout, .split { grid-template-columns: 1fr; }
      .launch-grid, .stats-grid, .trust-strip, .scenario-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
      .toolbar { grid-template-columns: 1fr; }
    }
    @media (max-width: 720px) {
      .shell { padding: 12px; }
      .section { padding: 14px; }
      .hero-card { padding: 18px; }
      .hero-title { font-size: 30px; }
      .launch-grid, .stats-grid, .trust-strip, .scenario-grid { grid-template-columns: 1fr; }
      .translator-row { grid-template-columns: 1fr; }
    }
  </style>
</head>
<body>
  <main class="shell">
    <section class="reveal">
      <div class="hero-grid">
        <div class="hero-card">
          <div class="eyebrow">Offline-first command center</div>
          <div class="hero-top">
            <h1 class="hero-title">Offgrid Kit</h1>
            <p class="hero-copy">A ready-to-use offline drive for knowledge, maps, translation, and local AI. Built for the person who just needs the answer, not a server manual.</p>
            <div class="meta-row">
              <div class="meta-pill"><strong>{{ total }}</strong> knowledge packs ready</div>
              <div class="meta-pill"><strong>{{ total_size }}</strong> local content</div>
              <div class="meta-pill"><strong>{{ roots_count }}</strong> storage roots scanned</div>
            </div>
            <div class="hero-actions">
              <a class="btn btn-accent" href="http://{{ host_ip }}:8080" target="_blank">Open Knowledge</a>
              <a class="btn btn-mint" href="http://{{ host_ip }}:8091">Open Maps</a>
              <a class="btn btn-soft" href="http://{{ host_ip }}:8092" target="_blank">Open AI</a>
              <a class="btn btn-soft" href="/updates">Updates</a>
              <a class="btn btn-soft" href="#translator">Translate</a>
            </div>
            <div class="hero-note">
              {{ translator_status }}
              {% if sync_msg %}<br><strong>Latest sync:</strong> {{ sync_msg }}{% endif %}
            </div>
            <div class="trust-strip" aria-label="Product promises">
              <div class="trust-card"><strong>No account</strong>Runs locally after setup with no cloud login.</div>
              <div class="trust-card"><strong>No Docker required</strong>Designed for direct USB launchers and bundled services.</div>
              <div class="trust-card"><strong>Manual updates</strong>Checks only when asked and preserves user content.</div>
              <div class="trust-card"><strong>Paper backup</strong>Printable field cards for power outages and handoff.</div>
            </div>
          </div>
        </div>

        <aside class="system-rail glass">
          <div class="system-head">
            <div>
              <h2 style="margin:0 0 4px 0;">Ready to use</h2>
              <p class="muted small">The essentials, in plain language.</p>
            </div>
            <button id="themeToggle" class="btn btn-soft theme-toggle" type="button" onclick="toggleTheme()">🌙 Dark</button>
          </div>
          <div class="system-list">
            <div class="system-item">
              <label>Reading library</label>
              <strong>{{ loaded_count }} knowledge packs are ready to open</strong>
              <div class="small muted">Choose Knowledge to start browsing offline.</div>
            </div>
            <div class="system-item">
              <label>Translation</label>
              <strong>{{ translator_status }}</strong>
              <div class="small muted">Useful for emergency phrases or everyday conversation.</div>
            </div>
            <div class="system-item">
              <label>Assistant</label>
              <strong>{{ ai_status.label }}</strong>
              <div class="small muted">Ask questions in plain language when you need help fast.</div>
            </div>
          </div>
        </aside>
      </div>
    </section>

    <section class="glass section reveal">
      <div class="section-head">
        <div>
          <h2>Start here</h2>
          <p class="subcopy">The four things people reach for first, made obvious and fast.</p>
        </div>
      </div>
      <div class="scenario-grid" aria-label="Common situations">
        <a class="scenario-card" href="/field-cards" target="_blank"><strong>Power is out</strong><span>Print or open quick cards before batteries matter.</span></a>
        <a class="scenario-card" href="/go/firstaid" target="_blank"><strong>Someone is hurt</strong><span>Jump straight into first-aid references.</span></a>
        <a class="scenario-card" href="/go/maps"><strong>Need directions</strong><span>Open the local map manager without searching menus.</span></a>
        <a class="scenario-card" href="/offline-proof" target="_blank"><strong>Prove it is local</strong><span>Show installed counts, URLs, and privacy posture.</span></a>
      </div>
      <div class="launch-grid">
        <a class="launch-card card-knowledge" href="http://{{ host_ip }}:8080" target="_blank">
          <div class="launch-kicker">Read</div>
          <div class="launch-title">Knowledge</div>
          <div class="launch-copy">Open the offline reader with the current ZIM stack.</div>
        </a>
        <a class="launch-card card-maps" href="http://{{ host_ip }}:8091">
          <div class="launch-kicker">Navigate</div>
          <div class="launch-title">Maps</div>
          <div class="launch-copy">Browse local PMTiles datasets and search towns offline.</div>
        </a>
        <a class="launch-card card-library" href="/ebooks">
          <div class="launch-kicker">Browse</div>
          <div class="launch-title">Library</div>
          <div class="launch-copy">Find PDFs and ebooks living alongside the knowledge kit.</div>
        </a>
        <a class="launch-card card-help" href="/help">
          <div class="launch-kicker">Support</div>
          <div class="launch-title">Help & recovery</div>
          <div class="launch-copy">Get URLs, service checks, and install troubleshooting fast.</div>
        </a>
        <a class="launch-card card-maps" href="/setup">
          <div class="launch-kicker">First run</div>
          <div class="launch-title">Setup check</div>
          <div class="launch-copy">Prepare folders, verify the bundle, and confirm the kit is ready.</div>
        </a>
        <a class="launch-card card-help" href="/updates">
          <div class="launch-kicker">Maintain</div>
          <div class="launch-title">Updates</div>
          <div class="launch-copy">Manually check the official update manifest when internet is available.</div>
        </a>
        <a class="launch-card card-library" href="/field-cards" target="_blank">
          <div class="launch-kicker">Print</div>
          <div class="launch-title">Field Cards</div>
          <div class="launch-copy">Pocket-ready cards for power, water, first aid, maps, and radio notes.</div>
        </a>
        <a class="launch-card card-knowledge" href="/offline-proof" target="_blank">
          <div class="launch-kicker">Verify</div>
          <div class="launch-title">Offline Proof</div>
          <div class="launch-copy">Show what is installed, local, private, and ready without internet.</div>
        </a>
      </div>
      <div class="toolbar" style="margin-top:4px; grid-template-columns: 1fr auto;">
        <input id="extraDir" class="input" type="text" placeholder="Optional extra folder to include in scans" value="{{ scan_dir }}" />
        <button class="btn btn-accent" onclick="rescan()">Refresh library</button>
      </div>
      <p class="subcopy">Scanning roots: {{ roots|join(' • ') }}</p>
    </section>

    <section class="glass section reveal feature feature-ai">
      <div style="display:flex; justify-content:space-between; gap:16px; align-items:flex-start; flex-wrap:wrap;">
        <div>
          <h2>Ask the assistant</h2>
          <p class="subcopy">Type a question naturally. The system answers locally without needing internet.</p>
        </div>
        <div class="status-pill"><span class="dot {{ 'warn' if not ai_status.ok else '' }}"></span><span id="aiStatusLabel">{{ ai_status.label }}</span></div>
      </div>
      <p id="aiStatusDetail" class="subcopy" style="margin-top:8px;">{{ ai_status.detail }}</p>

      <div class="chat-shell" id="miniAiShell">
        <div id="miniAiOutput" class="chat-output"><div class="chat-bubble assistant">Offline AI ready.</div></div>
        <div id="miniAiSpinner" class="chat-spinner"><span class="spinner-dot"></span><span class="spinner-dot"></span><span class="spinner-dot"></span><span>Thinking locally…</span></div>
        <div style="display:flex; gap:12px; align-items:center; margin-top:14px; flex-wrap:wrap;">
          <span id="miniAiModelStatus" class="muted">{{ ai_status.detail }}</span>
        </div>
        <textarea id="miniAiPrompt" class="textarea" style="min-height:110px; margin-top:14px;" placeholder="Ask a question in plain language..."></textarea>
        <div class="suggestion-row">
          <button class="chip prompt-chip" type="button" onclick='fillMiniAiPrompt("How do I purify water safely?")'>Purify water</button>
          <button class="chip prompt-chip" type="button" onclick='fillMiniAiPrompt("What are the first steps for basic first aid?")'>First aid</button>
          <button class="chip prompt-chip" type="button" onclick='fillMiniAiPrompt("Give me a simple checklist for shelter tonight.")'>Shelter checklist</button>
        </div>
        <div class="soft-note">Ask short, direct questions for the fastest answers.</div>
        <div style="display:flex; justify-content:flex-end; margin-top:12px;">
          <button id="miniAiSend" class="btn btn-accent" type="button">Send</button>
        </div>
      </div>
    </section>

    <section class="layout">
      <div>
        <section class="glass section reveal feature feature-library">
          <div class="section-head"><div><h2>Library</h2><p class="subcopy">Open the local knowledge packs without worrying about filenames or folders.</p></div></div>
          <div class="toolbar">
            <input id="q" class="input" type="text" placeholder="Filter by title, category, or path… (press / to focus)" oninput="quickFilter()" />
            <select id="sortMode" class="select" onchange="sortRows()">
              <option value="title_asc">Title A→Z</option>
              <option value="title_desc">Title Z→A</option>
              <option value="size_desc">Size ↓</option>
              <option value="size_asc">Size ↑</option>
            </select>
            <button class="btn btn-soft" onclick="clearFilters()">Clear</button>
          </div>

          <div class="chips">
            <button class="chip active" data-cat="all" onclick="setCategory('all', this)">All</button>
            <button class="chip" onclick="setCategory('Wikipedia', this)">Wikipedia</button>
            <button class="chip" onclick="setCategory('Medical', this)">Medical</button>
            <button class="chip" onclick="setCategory('Travel', this)">Travel</button>
            <button class="chip" onclick="setCategory('Dictionary', this)">Dictionary</button>
            <button class="chip" onclick="setCategory('Maps', this)">Maps</button>
            <button class="chip" onclick="setCategory('Other', this)">Other</button>
            <span class="visible-count">Visible: <strong id="visibleCount">0</strong></span>
          </div>

          <div class="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Title</th>
                  <th>Category</th>
                  <th>Size</th>
                  <th>Open</th>
                </tr>
              </thead>
              <tbody>
                {% for z in zims %}
                <tr data-search="{{ (z.title + ' ' + z.category + ' ' + z.path).lower() }}" data-category="{{ z.category }}" data-title="{{ z.title.lower() }}" data-size-bytes="{{ z.size_bytes }}">
                  <td><div><strong>{{ z.icon }} {{ z.title }}</strong></div><div class="file-name">{{ z.filename }}</div></td>
                  <td><span class="badge">{{ z.category }}</span></td>
                  <td class="muted">{{ z.size }}</td>
                  <td><a class="btn btn-accent" style="min-height:36px;padding:8px 12px;font-size:12px;" href="{{ z.open_url }}" target="_blank">Open</a></td>
                </tr>
                {% endfor %}
              </tbody>
            </table>
          </div>
        </section>

        <section id="wiki-search" class="glass section reveal feature feature-search">
          <h2>Find in the library</h2>
          <p class="subcopy">Search your offline collection and pull out the useful part quickly.</p>
          <div class="toolbar" style="margin-top:16px; grid-template-columns: 1fr auto;">
            <input id="wikiQ" class="input" type="text" placeholder="Search the offline library (e.g. water purification)" />
            <button class="btn btn-accent" type="button" onclick="wikiSearch()">Search</button>
          </div>
          <div class="split">
            <div id="wikiResults" class="panel-box">
              {% if wiki_results and wiki_results|length > 0 %}
                {% for r in wiki_results %}
                  <div class="search-item">
                    <div class="search-title">{{ loop.index }}. {{ r.title }}</div>
                    <div class="muted small"><a href="{{ r.url }}" target="_blank">Open full article</a></div>
                    <button class="btn btn-soft" style="margin-top:8px; min-height:36px; padding:8px 12px; font-size:12px;" onclick='wikiParse({{ r.url|tojson }})'>Parse excerpt</button>
                  </div>
                {% endfor %}
              {% else %}
                <div class="muted">Run a query to see results.</div>
              {% endif %}
            </div>
            <div id="wikiParsed" class="panel-box" style="white-space:pre-wrap;"></div>
          </div>
        </section>
      </div>

      <aside class="side-stack">
        <section class="glass section reveal feature feature-emergency">
          <h2>Emergency shortcuts</h2>
          <div class="quick-grid" style="margin-top:16px;">
            <a class="btn btn-soft" href="/go/water" target="_blank">Water Purification</a>
            <a class="btn btn-soft" href="/go/firstaid" target="_blank">First Aid</a>
            <a class="btn btn-soft" href="/go/shelter" target="_blank">Shelter</a>
            <a class="btn btn-soft" href="/?qa=translate#translator">Emergency Phrase</a>
          </div>
          <p id="quickActionStatus" class="subcopy">{{ qa_status or 'One-tap links for the things people need most under stress.' }}</p>
        </section>

        <section id="translator" class="glass section reveal feature feature-translate">
          <h2>Translator</h2>
          <p class="subcopy">Clean offline translation for emergency and everyday use.</p>
          <form id="translateForm" method="post" action="/translate_form" style="margin-top:16px;">
            <div class="translator-row">
              <select id="trSource" name="source" class="select">
                {% for c in language_options %}
                  <option value="{{ c.code }}" {% if c.code == tr_source %}selected{% endif %}>{{ c.label }}</option>
                {% endfor %}
              </select>
              <button class="btn btn-soft" type="button" onclick="swapTranslatorLangs()">⇄</button>
              <select id="trTarget" name="target" class="select">
                {% for c in language_options %}
                  <option value="{{ c.code }}" {% if c.code == tr_target %}selected{% endif %}>{{ c.label }}</option>
                {% endfor %}
              </select>
            </div>
            <textarea id="trInput" name="text" class="textarea" style="margin-top:12px;" placeholder="Type what one person says, or paste any text...">{{ tr_input }}</textarea>
            <div class="button-row" style="margin-top:12px;">
              <button class="btn btn-accent" type="submit" formaction="/translate_form">Translate</button>
              <button class="btn btn-soft" type="button" onclick="document.getElementById('trInput').value = document.getElementById('trOutput').value || ''">Use Output as Next Input</button>
            </div>
          </form>
          <textarea id="trOutput" class="textarea" style="margin-top:12px;" placeholder="Translation output..." readonly>{{ tr_output }}</textarea>
          <p id="trMeta" class="subcopy">{{ tr_meta }}</p>
        </section>



      </aside>
    </section>
  </main>
</body>
</html>
"""

HELP_HTML = """
<!doctype html><html><head><meta charset='utf-8'><title>Offline Help</title><style>:root{--bg:#f4f6fb;--card:#fff;--line:#dbe2ef;--text:#1f2937;--muted:#6b7280;--accent:#0a84ff}[data-theme="dark"]{--bg:#08111f;--card:#0f1a2d;--line:#22324b;--text:#ecf3ff;--muted:#9eb1cc;--accent:#7dd3fc}body{font-family:Inter,Arial,sans-serif;max-width:960px;margin:30px auto;padding:0 16px;color:var(--text);background:var(--bg)}.card{border:1px solid var(--line);background:var(--card);border-radius:16px;padding:16px;margin-bottom:14px}.muted{color:var(--muted)}code,pre{background:rgba(10,132,255,.08);padding:2px 6px;border-radius:6px}a{color:var(--accent)}.top{display:flex;justify-content:space-between;gap:12px;align-items:flex-start;flex-wrap:wrap}.btn{border:1px solid var(--line);border-radius:10px;padding:8px 12px;background:var(--card);color:var(--text);cursor:pointer;text-decoration:none}</style><script>function applyTheme(t){document.documentElement.setAttribute('data-theme',t==='dark'?'dark':'light');const b=document.getElementById('themeToggle');if(b)b.textContent=t==='dark'?'☀️ Light':'🌙 Dark'}function toggleTheme(){const c=document.documentElement.getAttribute('data-theme')==='dark'?'dark':'light';const n=c==='dark'?'light':'dark';localStorage.setItem('wikiTheme',n);applyTheme(n)}document.addEventListener('DOMContentLoaded',()=>applyTheme(localStorage.getItem('wikiTheme')||'light'));</script></head><body>
<div class='top'><div><h1>Help</h1><p class='muted'>Simple answers for common tasks.</p></div><div><button id='themeToggle' class='btn' onclick='toggleTheme()'>🌙 Dark</button> <a class='btn' href='/'>Back</a></div></div>
<div class='card'><h2>Where do I start?</h2><p class='muted'>Use the dashboard for most things. Knowledge opens the reader, Maps opens offline maps, and Translate helps with emergency phrases and everyday language.</p></div>
<div class='card'><h2>Main addresses</h2><ul><li>Dashboard: <code>:8090</code></li><li>Knowledge: <code>:8080</code></li><li>Maps: <code>:8091</code></li><li>Assistant: <code>:8092</code></li></ul></div>
<div class='card'><h2>Printable handoff tools</h2><ul><li><a href='/field-cards'>Field Cards</a> for paper/pocket emergency use.</li><li><a href='/offline-proof'>Offline Proof</a> for confirming local content and privacy claims.</li></ul></div>
<div class='card'><h2>If something seems missing</h2><ul><li>Try the dashboard first and refresh once.</li><li>If translation is blank, the language pack may not be installed yet.</li><li>If a page will not open, restarting the kit usually fixes it.</li></ul></div>
</body></html>
"""

EBOOKS_HTML = """
<!doctype html><html><head><meta charset='utf-8'><title>Offline Library</title>
<style>:root{--bg:#f4f6fb;--card:#fff;--line:#dbe2ef;--text:#1f2937;--muted:#6b7280;--accent:#0a84ff}[data-theme="dark"]{--bg:#08111f;--card:#0f1a2d;--line:#22324b;--text:#ecf3ff;--muted:#9eb1cc;--accent:#7dd3fc}body{font-family:Inter,Arial,sans-serif;max-width:1100px;margin:24px auto;padding:0 16px;color:var(--text);background:var(--bg)}h1{margin-bottom:6px}.muted{color:var(--muted)}.card{border:1px solid var(--line);background:var(--card);border-radius:16px;padding:16px;margin-bottom:12px}a{color:var(--accent)}.row{padding:10px 0;border-bottom:1px solid var(--line)}.path{font-size:12px;color:var(--muted)}.top{display:flex;justify-content:space-between;gap:12px;align-items:flex-start;flex-wrap:wrap}.btn{border:1px solid var(--line);border-radius:10px;padding:8px 12px;background:var(--card);color:var(--text);cursor:pointer;text-decoration:none}</style><script>function applyTheme(t){document.documentElement.setAttribute('data-theme',t==='dark'?'dark':'light');const b=document.getElementById('themeToggle');if(b)b.textContent=t==='dark'?'☀️ Light':'🌙 Dark'}function toggleTheme(){const c=document.documentElement.getAttribute('data-theme')==='dark'?'dark':'light';const n=c==='dark'?'light':'dark';localStorage.setItem('wikiTheme',n);applyTheme(n)}document.addEventListener('DOMContentLoaded',()=>applyTheme(localStorage.getItem('wikiTheme')||'light'));</script></head><body>
<div class='top'><div><h1>Library</h1><div class='muted'>Books and documents stored with the offline kit.</div></div><div><button id='themeToggle' class='btn' onclick='toggleTheme()'>🌙 Dark</button> <a class='btn' href='/'>Back</a></div></div>
<div class='card'>
  <div class='muted'>Add ebooks to any of these folders:</div>
  <ul>__ROOTS_HTML__</ul>
</div>
<div class='card'>
  __ROWS_HTML__
</div>
</body></html>
"""

SETUP_HTML = """
<!doctype html><html><head><meta charset='utf-8'><title>Setup Check</title>
<style>
:root{--bg:#f4f7fb;--card:#fff;--line:#d9e1ee;--text:#172033;--muted:#657086;--blue:#0a84ff;--green:#0b7f5f;--amber:#9b6500}
*{box-sizing:border-box}body{font-family:Inter,Arial,sans-serif;max-width:1040px;margin:24px auto;padding:0 16px;color:var(--text);background:linear-gradient(135deg,#f8fbff,#eef5ff)}
h1{margin:0 0 6px;font-size:36px}.muted{color:var(--muted);line-height:1.5}.top{display:flex;justify-content:space-between;gap:12px;align-items:flex-start;flex-wrap:wrap;margin-bottom:14px}
.card{border:1px solid var(--line);background:rgba(255,255,255,.9);border-radius:20px;padding:18px;margin-bottom:12px;box-shadow:0 16px 38px rgba(24,36,58,.08)}
.steps{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px;margin-top:12px}.step{border:1px solid var(--line);border-radius:16px;background:#fff;padding:14px;text-align:left;cursor:pointer;color:var(--text)}
.step strong{display:block;margin-bottom:5px}.step span{display:block;color:var(--muted);font-size:13px;line-height:1.35}.step:hover{border-color:#aacfff}
.btn{border:1px solid var(--line);border-radius:12px;padding:9px 12px;background:#fff;color:var(--text);cursor:pointer;text-decoration:none;font-weight:700}.btn-primary{background:var(--blue);border-color:var(--blue);color:#fff}
.status-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px}.pill{border:1px solid var(--line);border-radius:14px;background:#f8fbff;padding:11px}.pill b{display:block;color:var(--green);margin-bottom:3px}
pre{border:1px solid var(--line);background:#f8fbff;border-radius:14px;padding:12px;white-space:pre-wrap;max-height:360px;overflow:auto}
@media(max-width:820px){.steps,.status-grid{grid-template-columns:1fr}.top{display:grid}h1{font-size:30px}}
</style>
<script>
async function runStep(action){
  const out=document.getElementById('out');
  out.textContent='Working...';
  const r=await fetch('/api/admin/action',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({action})});
  const d=await r.json();
  out.textContent=(d.ok?'OK: ':'CHECK: ')+(d.message||'')+'\n\n'+(d.output||'');
}
</script>
</head><body>
<div class='top'><div><h1>Setup Check</h1><p class='muted'>Use this page on a fresh machine before handing the kit to a tester or customer.</p></div><div><a class='btn' href='/'>Dashboard</a> <a class='btn btn-primary' href='/offline-proof'>Offline Proof</a></div></div>
<div class='card'>
  <h2>Fast launch check</h2>
  <p class='muted'>These actions are safe to run repeatedly. They prepare user folders, check services, verify shipped files, and import bundled USB content when present.</p>
  <div class='steps'>
    <button class='step' onclick="runStep('setup_dirs')"><strong>1. Prepare folders</strong><span>Create library folders without touching existing books, models, or ZIMs.</span></button>
    <button class='step' onclick="runStep('doctor')"><strong>2. Health check</strong><span>Check expected services and common launch problems.</span></button>
    <button class='step' onclick="runStep('verify')"><strong>3. Verify bundle</strong><span>Confirm shipped files match the checksum manifest.</span></button>
    <button class='step' onclick="runStep('sync_usb')"><strong>4. Import USB content</strong><span>Pull ZIMs from the configured USB source if available.</span></button>
  </div>
</div>
<div class='card'>
  <h2>What should pass before testing</h2>
  <div class='status-grid'>
    <div class='pill'><b>Dashboard opens</b><span class='muted'>Main screen loads at port 8090.</span></div>
    <div class='pill'><b>Knowledge opens</b><span class='muted'>Kiwix opens at port 8080 and search returns results.</span></div>
    <div class='pill'><b>User content preserved</b><span class='muted'>Models, ebooks, and ZIMs are never overwritten by updates.</span></div>
  </div>
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

FIELD_CARDS_HTML = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>Field Cards - Offgrid Kit</title>
  <style>
    :root{--ink:#172033;--muted:#657086;--line:#d9e1ee;--blue:#0a84ff;--green:#0b7f5f;--amber:#9b6500;--red:#a4342a}
    *{box-sizing:border-box}body{margin:0;background:#f4f7fb;color:var(--ink);font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Arial,sans-serif}.wrap{max-width:1120px;margin:0 auto;padding:24px 16px 40px}
    .top{display:flex;justify-content:space-between;gap:12px;align-items:flex-start;margin-bottom:14px}.muted{color:var(--muted);line-height:1.45}.btn{border:1px solid var(--line);border-radius:12px;background:#fff;color:var(--ink);padding:9px 12px;text-decoration:none;font-weight:700;cursor:pointer}h1{margin:0 0 6px;font-size:34px}h2{margin:0 0 8px;font-size:18px}
    .grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}.card{min-height:245px;border:1px solid var(--line);border-radius:18px;background:#fff;box-shadow:0 12px 32px rgba(24,36,58,.08);padding:16px;break-inside:avoid}.kicker{font-size:12px;text-transform:uppercase;letter-spacing:.08em;font-weight:900;color:var(--blue);margin-bottom:8px}.card ul{margin:0;padding-left:18px;line-height:1.5}.card li{margin:4px 0}.url{display:block;border:1px dashed var(--line);border-radius:10px;padding:8px;margin:8px 0;background:#f8fbff;overflow-wrap:anywhere;font-family:ui-monospace,Consolas,monospace;font-size:13px}.red{color:var(--red)}.green{color:var(--green)}.amber{color:var(--amber)}
    @media(max-width:760px){.grid{grid-template-columns:1fr}.top{display:grid}h1{font-size:28px}.card{min-height:auto}}
    @media print{body{background:#fff}.wrap{max-width:none;padding:8mm}.top .actions{display:none}.grid{grid-template-columns:repeat(2,1fr);gap:6mm}.card{box-shadow:none;border-color:#999;min-height:88mm;page-break-inside:avoid}.muted{color:#333}}
  </style>
</head>
<body>
  <main class="wrap">
    <div class="top">
      <div><h1>Field Cards</h1><p class="muted">Print these as a simple handoff sheet. They are fast prompts and local URLs, not professional emergency instructions.</p></div>
      <div class="actions"><button class="btn" onclick="print()">Print</button> <a class="btn" href="/">Dashboard</a></div>
    </div>
    <section class="grid">
      <article class="card"><div class="kicker">Start</div><h2>Open the kit</h2><span class="url">http://{{ host_ip }}:8090</span><ul><li>Use the dashboard first.</li><li>Open Knowledge for articles.</li><li>Open Maps for local map packs.</li><li>Use Safe OS eject after stopping services.</li></ul></article>
      <article class="card"><div class="kicker">Power</div><h2>Power outage checklist</h2><ul><li>Dim screen and close unused tabs.</li><li>Use Knowledge/Maps before AI to save battery.</li><li>Write down important answers in notes or paper.</li><li>Keep the USB connected until done.</li></ul></article>
      <article class="card"><div class="kicker">Water</div><h2>Water reference flow</h2><ul><li>Search: <strong>water purification</strong>.</li><li>Filter visible sediment first when possible.</li><li>Use local sources to confirm treatment time/dose.</li><li class="red">Do not guess on contamination or chemicals.</li></ul></article>
      <article class="card"><div class="kicker">Medical</div><h2>First-aid reference flow</h2><ul><li>Search: <strong>first aid</strong>.</li><li>Check breathing, severe bleeding, shock, and consciousness first.</li><li>Use references for details after immediate danger is stabilized.</li><li class="red">Call emergency services when available.</li></ul></article>
      <article class="card"><div class="kicker">Navigation</div><h2>Map flow</h2><span class="url">http://{{ host_ip }}:8091</span><ul><li>Mark current location and destination.</li><li>Check terrain before moving.</li><li>Use short route legs and confirm landmarks.</li><li>Keep paper notes of coordinates.</li></ul></article>
      <article class="card"><div class="kicker">Comms</div><h2>Translation and Morse</h2><ul><li>Translator: dashboard → Translate.</li><li>Morse tool: <span class="url">http://{{ host_ip }}:8090/morse</span></li><li>Send location, condition, needs, and time.</li><li>Keep messages short and repeatable.</li></ul></article>
      <article class="card"><div class="kicker">AI</div><h2>Ask better questions</h2><ul><li>Use short prompts.</li><li>Ask for checklists, warnings, and source terms.</li><li>Verify critical facts in Knowledge.</li><li class="amber">AI is a helper, not authority.</li></ul></article>
      <article class="card"><div class="kicker">Proof</div><h2>What this kit has</h2><ul><li>{{ loaded_count }} ZIM packs.</li><li>{{ ebook_count }} document files.</li><li>{{ model_count }} AI model file(s).</li><li class="green">Runs locally after setup; no account required.</li></ul></article>
    </section>
  </main>
</body>
</html>
"""

OFFLINE_PROOF_HTML = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>Offline Proof - Offgrid Kit</title>
  <style>
    :root{--ink:#172033;--muted:#657086;--line:#d9e1ee;--blue:#0a84ff;--green:#0b7f5f}
    *{box-sizing:border-box}body{margin:0;background:linear-gradient(135deg,#f8fbff,#eef5ff);color:var(--ink);font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Arial,sans-serif}.wrap{max-width:1040px;margin:0 auto;padding:26px 16px 42px}.top{display:flex;justify-content:space-between;gap:12px;align-items:flex-start;margin-bottom:14px}.muted{color:var(--muted);line-height:1.45}.btn{border:1px solid var(--line);border-radius:12px;background:#fff;color:var(--ink);padding:9px 12px;text-decoration:none;font-weight:700;cursor:pointer}h1{margin:0 0 6px;font-size:34px}h2{margin:0 0 8px;font-size:20px}.hero,.card{border:1px solid var(--line);border-radius:20px;background:rgba(255,255,255,.86);box-shadow:0 16px 38px rgba(24,36,58,.08);padding:18px}.hero{margin-bottom:12px}.stats{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px}.stat b{display:block;font-size:30px;color:var(--blue)}.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px;margin-top:12px}.card ul{margin:0;padding-left:18px;line-height:1.55}.url{display:block;border:1px dashed var(--line);border-radius:10px;padding:8px;margin:8px 0;background:#f8fbff;overflow-wrap:anywhere;font-family:ui-monospace,Consolas,monospace;font-size:13px}.pass{color:var(--green);font-weight:800}
    @media(max-width:760px){.stats,.grid{grid-template-columns:1fr}.top{display:grid}h1{font-size:28px}}
    @media print{body{background:#fff}.top .actions{display:none}.hero,.card{box-shadow:none;border-color:#999;break-inside:avoid}}
  </style>
</head>
<body>
  <main class="wrap">
    <div class="top">
      <div><h1>Offline Proof</h1><p class="muted">A buyer-facing proof page showing what is local, private, and ready on this machine.</p></div>
      <div class="actions"><button class="btn" onclick="print()">Print</button> <a class="btn" href="/">Dashboard</a></div>
    </div>
    <section class="hero">
      <h2>Installed locally</h2>
      <div class="stats">
        <div class="stat"><b>{{ loaded_count }}</b><span class="muted">ZIM packs</span></div>
        <div class="stat"><b>{{ ebook_count }}</b><span class="muted">Documents</span></div>
        <div class="stat"><b>{{ model_count }}</b><span class="muted">AI models</span></div>
        <div class="stat"><b>{{ roots_count }}</b><span class="muted">Roots scanned</span></div>
      </div>
    </section>
    <section class="grid">
      <article class="card"><h2>Local URLs</h2><span class="url">Dashboard: http://{{ host_ip }}:8090</span><span class="url">Knowledge: http://{{ host_ip }}:8080</span><span class="url">Maps: http://{{ host_ip }}:8091</span><span class="url">AI: http://{{ host_ip }}:8092</span></article>
      <article class="card"><h2>Privacy posture</h2><ul><li class="pass">No cloud account required.</li><li class="pass">Local Kiwix, maps, translation, and llama.cpp services.</li><li>LAN exposure depends on how the user launches/services bind.</li><li>No telemetry code is required for the dashboard workflow.</li></ul></article>
      <article class="card"><h2>Support status</h2><ul><li>{{ health_summary }}</li><li>{{ translator_status }}</li><li>{{ ai_status.label }}: {{ ai_status.detail }}</li></ul></article>
      <article class="card"><h2>USB product advantage</h2><ul><li>Designed as a handoff kit, not just a server installer.</li><li>Works from bundled content instead of forcing a fresh download.</li><li>Includes printable field cards for non-technical users.</li></ul></article>
    </section>
  </main>
</body>
</html>
"""

UPDATES_HTML = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>Updates - Offgrid Kit</title>
  <style>
    :root{--ink:#172033;--muted:#657086;--line:#d9e1ee;--blue:#0a84ff;--green:#0b7f5f;--red:#a4342a;--amber:#9b6500}
    *{box-sizing:border-box}body{margin:0;background:linear-gradient(135deg,#f8fbff,#eef5ff);color:var(--ink);font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Arial,sans-serif}.wrap{max-width:980px;margin:0 auto;padding:26px 16px 42px}.top{display:flex;justify-content:space-between;gap:12px;align-items:flex-start;margin-bottom:14px}.muted{color:var(--muted);line-height:1.45}.btn{border:1px solid var(--line);border-radius:12px;background:#fff;color:var(--ink);padding:9px 12px;text-decoration:none;font-weight:700;cursor:pointer}.btn-primary{background:var(--blue);border-color:var(--blue);color:#fff}h1{margin:0 0 6px;font-size:34px}h2{margin:0 0 8px;font-size:20px}.card{border:1px solid var(--line);border-radius:20px;background:rgba(255,255,255,.9);box-shadow:0 16px 38px rgba(24,36,58,.08);padding:18px;margin-bottom:12px}.row{display:grid;grid-template-columns:190px 1fr;gap:12px;padding:10px 0;border-bottom:1px solid var(--line)}.row:last-child{border-bottom:0}.status{border-radius:14px;padding:12px;background:#f8fbff;border:1px solid var(--line);margin-top:12px}.status.ok strong{color:var(--green)}.status.warn strong{color:var(--amber)}.status.bad strong{color:var(--red)}code{background:#f1f5fb;border:1px solid var(--line);border-radius:7px;padding:2px 5px;overflow-wrap:anywhere}.actions{display:flex;gap:8px;flex-wrap:wrap}.details{white-space:pre-wrap}
    @media(max-width:680px){.top,.row{display:grid;grid-template-columns:1fr}h1{font-size:28px}}
  </style>
</head>
<body>
  <main class="wrap">
    <div class="top">
      <div><h1>Updates</h1><p class="muted">Manual checks only. Nothing installs automatically.</p></div>
      <div class="actions"><button class="btn btn-primary" onclick="checkUpdates()">Check Now</button><a class="btn" href="/">Dashboard</a></div>
    </div>
    <section class="card">
      <h2>Current kit</h2>
      <div class="row"><strong>Product</strong><span>{{ current.name }}</span></div>
      <div class="row"><strong>Version</strong><span>{{ current.version }}</span></div>
      <div class="row"><strong>Updated</strong><span>{{ current.updated }}</span></div>
      <div class="row"><strong>Channel</strong><span>{{ current.channel or 'stable' }}</span></div>
      <div class="row"><strong>Update source</strong><span><code>{{ update_source or 'not configured' }}</code></span></div>
      <div class="status warn"><strong>Policy:</strong> Offgrid Kit never auto-updates. User content in <code>models/</code>, <code>ebooks/</code>, and <code>zims/</code> is preserved.</div>
    </section>
    <section class="card">
      <h2>Check result</h2>
      <div id="updateResult" class="status">Click <strong>Check Now</strong> when internet is available.</div>
    </section>
  </main>
  <script>
    async function checkUpdates(){
      const box = document.getElementById('updateResult');
      box.className = 'status';
      box.textContent = 'Checking official update manifest...';
      try {
        const res = await fetch('/api/update/check');
        const data = await res.json();
        const latest = data.latest || {};
        box.className = 'status ' + (data.ok ? (data.update_available ? 'warn' : 'ok') : 'bad');
        let html = '<strong>' + (data.message || 'Update check finished.') + '</strong>';
        if (data.ok) {
          html += '<div class="details">Latest: ' + (latest.version || 'unknown') + '\\nUpdated: ' + (latest.updated || 'unknown') + '\\nSummary: ' + (latest.summary || 'No notes supplied.') + '</div>';
          if (data.online === false && data.online_error) html += '<p class="muted">Online source unavailable; checked bundled manifest instead. Online error: <code>' + data.online_error + '</code></p>';
          if (latest.release_notes_url) html += '<p><a href="' + latest.release_notes_url + '" target="_blank">Release notes</a></p>';
          if (latest.download_url) html += '<p><a href="' + latest.download_url + '" target="_blank">Download update</a></p>';
          if (latest.checksum_sha256) html += '<p class="muted">Expected SHA-256: <code>' + latest.checksum_sha256 + '</code></p>';
        } else if (data.source) {
          html += '<p class="muted">Source: <code>' + data.source + '</code></p>';
        }
        box.innerHTML = html;
      } catch (err) {
        box.className = 'status bad';
        box.innerHTML = '<strong>Update check failed.</strong><p class="muted">' + err + '</p>';
      }
    }
  </script>
</body>
</html>
"""

AI_BASE = os.environ.get("AI_BASE", f"http://127.0.0.1:{os.environ.get('LLAMA_PORT', '8092')}")
AI_MODEL_Q8 = os.environ.get("LLAMA_MODEL_Q8", str(KIT_ROOT / "models/local-qwen/Huihui-Qwen3.5-4B-abliterated.Q8_0.gguf"))
AI_MODEL_Q4 = os.environ.get("LLAMA_MODEL_Q4", str(KIT_ROOT / "models/local-qwen/Huihui-Qwen3.5-4B-abliterated.Q4_K_M.gguf"))
AI_MODELS_DIR = Path(os.environ.get("AI_MODELS_DIR", str(KIT_ROOT / "models/local-qwen")))
AI_MODEL = os.environ.get("LLAMA_MODEL", AI_MODEL_Q8)
AI_MODEL_NAME = os.environ.get("AI_MODEL_NAME", "local-model")
AI_TIMEOUT = float(os.environ.get("AI_TIMEOUT", "600"))
SET_MODEL_SCRIPT = KIT_ROOT / "scripts/set_llama_model.sh"

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


def read_version_info() -> dict:
    fallback = {
        "name": "offgrid-kit",
        "version": "1.0.0",
        "updated": "2026-06-25",
        "channel": "stable",
        "update_manifest_url": DEFAULT_UPDATE_MANIFEST_URL,
    }
    try:
        if VERSION_FILE.exists():
            data = json.loads(VERSION_FILE.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return {**fallback, **data}
    except Exception:
        pass
    return fallback


def update_manifest_url() -> str:
    return (
        os.environ.get("OFFGRID_UPDATE_MANIFEST_URL")
        or read_version_info().get("update_manifest_url")
        or DEFAULT_UPDATE_MANIFEST_URL
    ).strip()


def parse_version_tuple(value: str) -> tuple:
    parts = re.findall(r"\d+", value or "")
    return tuple(int(p) for p in parts[:4]) if parts else (0,)


def update_result_from_manifest(remote: dict, current: dict, source: str, policy: str, online: bool = True, message_prefix: str = "") -> dict:
    latest = str(remote.get("version") or remote.get("latest_version") or "")
    update_available = parse_version_tuple(latest) > parse_version_tuple(str(current.get("version") or ""))
    message = "Update available." if update_available else "This kit is up to date."
    if message_prefix:
        message = f"{message_prefix} {message}"
    return {
        "ok": True,
        "configured": True,
        "online": online,
        "source": source,
        "current": current,
        "latest": {
            "version": latest,
            "updated": remote.get("updated") or remote.get("date") or "",
            "channel": remote.get("channel") or "",
            "summary": remote.get("summary") or remote.get("notes") or "",
            "release_notes_url": remote.get("release_notes_url") or "",
            "download_url": remote.get("download_url") or "",
            "checksum_sha256": remote.get("checksum_sha256") or "",
        },
        "update_available": update_available,
        "policy": policy,
        "message": message,
    }


def check_update_manifest() -> dict:
    current = read_version_info()
    url = update_manifest_url()
    policy = "Manual check only. Offgrid Kit never auto-updates and preserves user content in models/, ebooks/, and zims/."
    if not url:
        return {
            "ok": False,
            "configured": False,
            "current": current,
            "policy": policy,
            "message": "No update manifest URL is configured.",
        }
    try:
        response = requests.get(url, timeout=12, headers={"User-Agent": "OffgridKitUpdater/1.0"})
        response.raise_for_status()
        remote = response.json()
        if not isinstance(remote, dict):
            raise ValueError("Update manifest must be a JSON object.")
        return update_result_from_manifest(remote, current, url, policy, online=True)
    except Exception as exc:
        try:
            if LOCAL_UPDATE_MANIFEST_FILE.exists():
                local = json.loads(LOCAL_UPDATE_MANIFEST_FILE.read_text(encoding="utf-8"))
                if isinstance(local, dict):
                    result = update_result_from_manifest(
                        local,
                        current,
                        str(LOCAL_UPDATE_MANIFEST_FILE),
                        policy,
                        online=False,
                        message_prefix="Online update source unavailable; using bundled manifest.",
                    )
                    result["online_error"] = str(exc)
                    result["online_source"] = url
                    return result
        except Exception:
            pass
        return {
            "ok": False,
            "configured": True,
            "source": url,
            "current": current,
            "policy": policy,
            "message": f"Update check failed: {exc}",
        }


def build_roots(extra: str):
    roots = []
    for p in DEFAULT_ROOTS:
        try:
            if p.exists() and p.is_dir():
                roots.append(p)
        except Exception:
            continue
    if extra:
        ep = Path(extra)
        try:
            if ep.exists() and ep.is_dir() and ep not in roots:
                roots.append(ep)
        except Exception:
            pass
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


def resolve_ai_model(choice: str | None = None) -> str:
    choice_raw = (choice or '').strip()
    choice_l = choice_raw.lower()
    if choice_l == 'q4':
        return AI_MODEL_Q4
    if choice_l == 'q8':
        return AI_MODEL_Q8
    if choice_raw:
        p = Path(choice_raw)
        if not p.is_absolute():
            p = AI_MODELS_DIR / p
        try:
            return str(p.resolve())
        except Exception:
            return str(p)
    return AI_MODEL


def discover_ai_models():
    out = []
    try:
        if AI_MODELS_DIR.exists():
            for p in sorted(AI_MODELS_DIR.rglob("*.gguf")):
                try:
                    rp = p.resolve()
                except Exception:
                    rp = p
                out.append({"name": p.name, "path": str(rp)})
    except Exception:
        pass
    if not out:
        out = [{"name": Path(AI_MODEL).name, "path": AI_MODEL}]
    return out


def _model_allowed(model_path: Path) -> bool:
    try:
        base = AI_MODELS_DIR.resolve()
        rp = model_path.resolve()
        return rp == base or base in rp.parents
    except Exception:
        return False


def _llama_model_id() -> str:
    try:
        r = requests.get(f"{AI_BASE}/v1/models", timeout=5)
        if r.ok:
            data = r.json() or {}
            models = data.get("data") or []
            if models and isinstance(models, list):
                mid = models[0].get("id")
                if mid:
                    return str(mid)
    except Exception:
        pass
    return AI_MODEL_NAME


def current_selected_model_path() -> str:
    envf = Path("/etc/default/wiki-offline-kit")
    try:
        if envf.exists():
            for line in envf.read_text().splitlines():
                if line.startswith("LLAMA_MODEL="):
                    return line.split("=", 1)[1].strip()
    except Exception:
        pass
    return AI_MODEL


def ai_status_info():
    try:
        r = requests.get(f"{AI_BASE}/v1/models", timeout=5)
        if r.ok:
            data = r.json()
            models = data.get("data") or []
            names = [m.get("id") for m in models if m.get("id")]
            selected = Path(current_selected_model_path()).name
            return {
                "ok": True,
                "label": f"AI online (llama.cpp)",
                "detail": f"server model(s): {', '.join(names[:3]) if names else 'reachable'} • selected file: {selected}",
                "models": names,
            }
    except Exception:
        pass
    return {
        "ok": False,
        "label": "AI offline",
        "detail": "Start local llama-server service to enable offline AI.",
        "models": [],
    }


def clean_ai_output(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r"<think>[\s\S]*?</think>", "", text, flags=re.IGNORECASE)
    text = re.sub(r"<\|[^>]+\|>", "", text)
    text = re.sub(r"<\/?think>", "", text, flags=re.IGNORECASE)
    text = text.replace("’", "'")
    lines = [ln.rstrip() for ln in text.splitlines()]
    cleaned = []
    for ln in lines:
        if not cleaned or ln != cleaned[-1]:
            cleaned.append(ln)
    text = "\n".join(cleaned)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    return text.strip()


def ai_chat(prompt: str, mode: str = "general", context: str = "", model_choice: str | None = None):
    system_map = {
        "general": "You are an offline local AI assistant inside an offgrid knowledge console. Be useful, clear, calm, and direct. Support general prompts and optionally help interpret pasted wiki excerpts. Avoid dangerous, illegal, deceptive, or harmful instructions.",
        "survival": "You are an offline local AI assistant inside an offgrid knowledge console. Be useful, clear, calm, and direct. Support general prompts and optionally help interpret pasted wiki excerpts. Avoid dangerous, illegal, deceptive, or harmful instructions.",
        "summarize": "You are an offline local AI assistant inside an offgrid knowledge console. Summarize clearly and compactly while preserving important facts and practical details.",
        "explain": "You are an offline local AI assistant inside an offgrid knowledge console. Explain clearly in simple language with useful structure and examples when appropriate.",
    }
    system = system_map.get(mode, system_map["general"])
    user_prompt = prompt.strip()
    if context.strip():
        user_prompt = f"Context:\n{context.strip()}\n\nUser request:\n{user_prompt}"

    model_name = _llama_model_id()
    payload = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user_prompt},
        ],
        "stream": False,
        "temperature": 0.2,
    }
    r = requests.post(f"{AI_BASE}/v1/chat/completions", json=payload, timeout=AI_TIMEOUT)
    r.raise_for_status()
    data = r.json()
    choices = data.get("choices") or []
    msg = (choices[0] or {}).get("message") if choices else {}
    return clean_ai_output((msg or {}).get("content", "").strip())


def health_summary_text():
    statuses = []
    for svc in ["kiwix.service", "zim-selector.service", "offline-map-ui.service", "llama-server.service"]:
        try:
            subprocess.check_call(["systemctl", "is-active", "--quiet", svc])
            statuses.append(f"{svc.split('.')[0]}:ok")
        except Exception:
            statuses.append(f"{svc.split('.')[0]}:check")
    ai = ai_status_info()
    statuses.append("ai:ok" if ai.get("ok") else "ai:offline")
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
    ai_status = ai_status_info()
    selected_ai_model = current_selected_model_path()
    ai_models = discover_ai_models()
    if selected_ai_model and all(m.get("path") != selected_ai_model for m in ai_models):
        ai_models.insert(0, {"name": Path(selected_ai_model).name, "path": selected_ai_model})
    ai_prompt = request.args.get("ai_prompt", "")
    ai_context = request.args.get("ai_context", "")
    ai_output = request.args.get("ai_output", "")

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
        ai_status=ai_status,
        ai_models=ai_models,
        ai_model=selected_ai_model,
        ai_model_name=Path(selected_ai_model).name,
        ai_prompt=ai_prompt,
        ai_context=ai_context,
        ai_output=ai_output,
    )


def proof_context(extra_scan_dir: str = ""):
    roots = build_roots(extra_scan_dir)
    paths = scan_zims(roots)
    _, ebooks = list_ebooks(limit=5000)
    models = discover_ai_models()
    return {
        "host_ip": host_ip(),
        "loaded_count": len(paths),
        "ebook_count": len(ebooks),
        "model_count": len(models),
        "roots_count": len(roots),
        "health_summary": health_summary_text(),
        "translator_status": translator_status_text()[0],
        "ai_status": ai_status_info(),
    }




AI_PAGE_HTML = """<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>Offline AI</title>
  <style>
    body { margin:0; font-family: Inter, system-ui, sans-serif; background:#0b1220; color:#eef4ff; }
    .wrap { max-width: 1180px; margin: 0 auto; padding: 24px; }
    .panel { background: rgba(255,255,255,.05); border:1px solid rgba(255,255,255,.08); border-radius:24px; padding:22px; box-shadow: 0 18px 50px rgba(0,0,0,.22); }
    .topbar { display:flex; justify-content:space-between; align-items:flex-start; gap:16px; flex-wrap:wrap; margin-bottom:16px; }
    .chat { min-height: 360px; max-height: 58vh; overflow:auto; display:flex; flex-direction:column; gap:12px; padding: 4px; border-radius:18px; background: rgba(255,255,255,.03); border:1px solid rgba(255,255,255,.06); }
    .bubble { padding:14px 16px; border-radius:18px; white-space:pre-wrap; line-height:1.7; max-width: 88%; }
    .assistant { background: rgba(255,255,255,.06); align-self:flex-start; }
    .user { background: rgba(125,211,252,.14); align-self:flex-end; }
    textarea { width:100%; box-sizing:border-box; border-radius:16px; border:1px solid rgba(255,255,255,.12); background:#101a2d; color:#eef4ff; padding:14px; }
    .prompt { min-height: 110px; }
    .context { min-height: 100px; margin-top: 12px; }
    .row { display:flex; gap:10px; margin-top:12px; flex-wrap:wrap; justify-content:flex-end; }
    button, a.btn { border:1px solid rgba(255,255,255,.12); background: rgba(255,255,255,.06); color:#eef4ff; border-radius:14px; padding:12px 16px; cursor:pointer; text-decoration:none; }
    button.primary { background: rgba(125,211,252,.15); }
    .muted { color:#9fb0cb; font-size:14px; }
  </style>
</head>
<body>
  <div class="wrap">
    <div class="panel">
      <div class="topbar">
        <div><h1 style="margin:0 0 8px 0;">Offline AI</h1><div class="muted">Simple local chat interface powered by {{ ai_status.detail or ai_model }}.</div></div>
        <div class="row" style="margin-top:0; justify-content:flex-start;"><a class="btn" href="/">Back to dashboard</a></div>
      </div>
      <div class="chat" id="chat">
        {% if prompt %}<div class="bubble user">{{ prompt }}</div>{% endif %}
        <div class="bubble assistant">{{ output or "Offline AI ready. Ask anything below." }}</div>
      </div>
      <form method="post" action="/ai">
        <textarea class="prompt" name="prompt" placeholder="Ask anything...">{{ prompt }}</textarea>
        <details style="margin-top:12px;"><summary class="muted">Optional context</summary><textarea class="context" name="context" placeholder="Paste optional supporting text here...">{{ context }}</textarea></details>
        <div class="row">
          <button class="primary" type="submit">Send</button>
        </div>
      </form>
    </div>
  </div>
</body>
</html>
"""


@app.route("/ai", methods=["GET", "POST"])
def ai_page():
    ai_status = ai_status_info()
    prompt = ""
    context = ""
    output = ""
    if request.method == "POST":
        prompt = (request.form.get("prompt") or "").strip()
        context = (request.form.get("context") or "").strip()
        if prompt:
            try:
                output = ai_chat(prompt, mode="general", context=context) or "No output returned."
            except Exception as e:
                output = f"Offline AI unavailable: {e}"
        else:
            output = "Enter a prompt first."
    return render_template_string(AI_PAGE_HTML, ai_status=ai_status, ai_model=AI_MODEL, prompt=prompt, context=context, output=output)
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


@app.get("/field-cards")
def field_cards_page():
    return render_template_string(FIELD_CARDS_HTML, **proof_context(request.args.get("scan_dir", "")))


@app.get("/offline-proof")
def offline_proof_page():
    return render_template_string(OFFLINE_PROOF_HTML, **proof_context(request.args.get("scan_dir", "")))


@app.get("/updates")
def updates_page():
    current = read_version_info()
    return render_template_string(UPDATES_HTML, current=current, update_source=update_manifest_url())


@app.get("/setup")
def setup_page():
    return SETUP_HTML


@app.get("/go/knowledge")
def go_knowledge():
    return redirect(f"http://{host_ip()}:8080")


@app.get("/go/maps")
def go_maps():
    return redirect(f"http://{host_ip()}:8091")


@app.get("/go/ai")
def go_ai():
    return redirect(f"http://{host_ip()}:8092")


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


@app.get("/api/update/check")
def api_update_check():
    return jsonify(check_update_manifest())


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


@app.get("/api/ai/status")
def api_ai_status():
    return jsonify(ai_status_info())


@app.get("/api/ai/models")
def api_ai_models():
    selected = current_selected_model_path()
    models = discover_ai_models()
    return jsonify({
        "ok": True,
        "selected": selected,
        "models": models,
    })


@app.post("/api/ai/model/select")
def api_ai_model_select():
    payload = request.get_json(silent=True) or {}
    raw_model = (payload.get("model") or "").strip()
    if not raw_model:
        return jsonify({"ok": False, "error": "Model is required."}), 400

    model_path = Path(resolve_ai_model(raw_model))
    if not model_path.exists() or not model_path.is_file() or model_path.suffix.lower() != ".gguf":
        return jsonify({"ok": False, "error": "Model file not found."}), 400
    if not _model_allowed(model_path):
        return jsonify({"ok": False, "error": f"Model must be inside {AI_MODELS_DIR}."}), 400
    if not SET_MODEL_SCRIPT.exists():
        return jsonify({"ok": False, "error": f"Missing helper script: {SET_MODEL_SCRIPT}"}), 500

    try:
        proc = subprocess.run(
            ["sudo", "-n", str(SET_MODEL_SCRIPT), str(model_path)],
            cwd=str(KIT_ROOT),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=120,
        )
    except Exception as e:
        return jsonify({"ok": False, "error": f"Switch failed: {e}"}), 500

    out = (proc.stdout or "").strip()
    if proc.returncode != 0:
        return jsonify({"ok": False, "error": out or "Failed to switch model."}), 500

    target_name = model_path.name
    status = ai_status_info()
    for _ in range(20):
        status = ai_status_info()
        detail = (status.get("detail") or "")
        if status.get("ok") and target_name in detail:
            break
        time.sleep(1)

    return jsonify({
        "ok": True,
        "message": f"Switched to {model_path.name}",
        "output": out,
        "status": status,
    })


@app.post("/ai_form")
def ai_form():
    prompt = (request.form.get("prompt") or "").strip()
    context = (request.form.get("context") or "").strip()
    output = "Enter a prompt first."
    if prompt:
        try:
            output = ai_chat(prompt, mode="general", context=context) or "No output returned."
        except Exception as e:
            output = f"Offline AI unavailable: {e}"
    params = {
        "ai_prompt": prompt,
        "ai_context": context,
        "ai_output": output,
    }
    from urllib.parse import urlencode
    return redirect('/?' + urlencode(params))


@app.post("/api/ai/stream")
def api_ai_stream():
    payload = request.get_json(silent=True) or {}
    prompt = (payload.get("prompt") or "").strip()
    context = (payload.get("context") or "").strip()
    model_choice = (payload.get("model_choice") or "q8").strip().lower()
    if not prompt:
        return ("Prompt is required.", 400)
    def generate():
        try:
            output = ai_chat(prompt, mode="general", context=context, model_choice=model_choice)
            yield output or "No output returned."
        except Exception as e:
            yield f"\n[stream error: {e}]"
    return Response(generate(), mimetype="text/plain")


@app.post("/api/ai/chat")
def api_ai_chat():
    payload = request.get_json(silent=True) or {}
    prompt = (payload.get("prompt") or "").strip()
    context = (payload.get("context") or "").strip()
    mode = (payload.get("mode") or "general").strip().lower()
    model_choice = (payload.get("model_choice") or "q8").strip().lower()
    if not prompt:
        return jsonify({"error": "Prompt is required."}), 400
    try:
        output = ai_chat(prompt, mode=mode, context=context, model_choice=model_choice)
        return jsonify({"ok": True, "output": output, "model": resolve_ai_model(model_choice)})
    except Exception as e:
        return jsonify({"ok": False, "error": f"Offline AI unavailable: {e}"}), 503


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
