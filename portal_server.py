#!/usr/bin/env python3
"""portal_server.py — Slate-grey LAN portal on port 8002.

Shows live status of PT, ultrathink, LM Studio Win/Mac, and Ollama Win/Mac.
All probes run concurrently via asyncio.gather.

Routes:
  GET  /           HTML dashboard (meta-refresh every 10s)
  GET  /api/status JSON status of all services
  POST /api/user-input  proxy to PT /user-input (portal textbox handler)
GET  /health     {"status": "ok", "version": "0.9.9.9"}
"""
from __future__ import annotations

import asyncio
import html as _html
import json
import logging
import os
import signal
import subprocess
import sys
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Load .env so IPs are correct whether portal is run from start.sh or directly.
try:
    from dotenv import load_dotenv as _load_dotenv
    _here = Path(__file__).parent
    _load_dotenv(_here / ".env",       override=False)
    _load_dotenv(_here / ".env.local", override=True)
except ImportError:
    pass

log = logging.getLogger("ultrathink.portal")
logging.basicConfig(level=logging.INFO)

VERSION = "0.9.9.9"

# ── IP Resolution (authoritative — reads openclaw.json, never stale hardcodes) ─
# Import shared resolver so portal works correctly whether started via start.sh
# or directly.  Priority chain: AlphaClaw live → openclaw.json → discovery.json
# → PT tilting → env var → subnet.103 constant.  See utils/ip_resolver.py.
try:
    import sys as _sys
    _sys.path.insert(0, str(Path(__file__).resolve().parent))
    from utils.ip_resolver import get_win_lms_url as _get_win_lms_url, get_win_ollama_url as _get_win_ollama_url, get_win_ip as _get_win_ip
    _WIN_LMS_DEFAULT  = _get_win_lms_url()
    _WIN_OLL_DEFAULT  = _get_win_ollama_url()
    _WIN_IP_LABEL     = _get_win_ip()
except Exception as _ip_exc:
    log.warning("ip_resolver import failed (%s) — using env/hardcoded fallback", _ip_exc)
    _WIN_LMS_DEFAULT  = "http://192.168.254.105:1234"
    _WIN_OLL_DEFAULT  = "http://192.168.254.105:11434"
    _WIN_IP_LABEL     = "192.168.254.105"

# ── Config ─────────────────────────────────────────────────────────────────────

PORTAL_HOST = os.getenv("PORTAL_HOST", "0.0.0.0")
PORTAL_PORT = int(os.getenv("PORTAL_PORT", "8002"))

PT_URL = os.getenv("ORCHESTRATOR_ENDPOINT", "http://localhost:8000")
US_URL = os.getenv("ULTRATHINK_ENDPOINT", "http://localhost:8001")

LMS_WIN_ENDPOINTS: List[str] = [
    ep.strip()
    for ep in os.getenv("LM_STUDIO_WIN_ENDPOINTS", _WIN_LMS_DEFAULT).split(",")
    if ep.strip()
]
LMS_MAC_ENDPOINT = os.getenv("LM_STUDIO_MAC_ENDPOINT", "http://localhost:1234")
LMS_API_TOKEN = os.getenv("LM_STUDIO_API_TOKEN", "")

OLLAMA_WIN = os.getenv("OLLAMA_WINDOWS_ENDPOINT", _WIN_OLL_DEFAULT)
OLLAMA_MAC = os.getenv("OLLAMA_MAC_ENDPOINT", "http://127.0.0.1:11434")
OPENROUTER_FREE_FALLBACKS = [
    "ollama/qwen3.5:9b-nvfp4",
    "openrouter/nvidia/nemotron-3-super-120b-a12b:free",
    "openrouter/minimax/minimax-m2.5:free",
    "openrouter/deepseek/deepseek-v4-flash:free",
    "openrouter/openai/gpt-oss-120b:free",
    "openrouter/z-ai/glm-4.5-air:free",
    "openrouter/inclusionai/ling-2.6-flash:free",
    "openrouter/openrouter/free",
]

PROBE_TIMEOUT = 3.0

REPO_ROOT = Path(__file__).resolve().parent
PERPETUA_TOOLS_ROOT = Path(
    os.getenv("PERPETUA_TOOLS_ROOT", REPO_ROOT.parent / "perplexity-api" / "Perpetua-Tools")
)


def _read_routing_json() -> dict:
    """Read PT's .state/routing.json for portal display."""
    import json as _json
    routing_path = PERPETUA_TOOLS_ROOT / ".state" / "routing.json"
    try:
        if routing_path.exists():
            return _json.loads(routing_path.read_text(encoding="utf-8"))
    except Exception:
        pass
    return {}


app = FastAPI(title="orama portal", version=VERSION)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── HTML template ──────────────────────────────────────────────────────────────

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>orama portal</title>
<style>
  *{{box-sizing:border-box;margin:0;padding:0}}
  body{{background:#475569;color:#f8fafc;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;font-size:14px;padding:1.5rem}}
  h1{{font-size:1.25rem;letter-spacing:.05em;margin-bottom:1rem;color:#38bdf8}}
  /* navbar */
  .navbar{{display:flex;justify-content:space-between;align-items:center;background:#1e293b;border-radius:4px;padding:.6rem 1rem;margin-bottom:1rem}}
  .nav-brand{{font-size:.95rem;font-weight:700;color:#38bdf8;letter-spacing:.04em}}
  .nav-links{{display:flex;gap:.75rem;align-items:center}}
  .nav-link{{color:#94a3b8;font-size:.8rem;text-decoration:none}}
  .nav-link:hover{{color:#f8fafc}}
  .theme-btn{{background:none;border:1px solid #475569;border-radius:3px;color:#94a3b8;cursor:pointer;font-size:.75rem;padding:.25rem .6rem}}
  .theme-btn:hover{{border-color:#38bdf8;color:#f8fafc}}
  /* night theme */
  body[data-theme="night"]{{background:#0f1117;color:#e2e8f0}}
  body[data-theme="night"] .navbar{{background:#111827}}
  body[data-theme="night"] .nav-brand{{color:#06b6d4}}
  body[data-theme="night"] h1{{color:#06b6d4}}
  body[data-theme="night"] .card{{background:#1a1d27;border-color:#2d3748}}
  body[data-theme="night"] .section-title{{color:#06b6d4;border-color:#06b6d440}}
  body[data-theme="night"] .url{{color:#06b6d4}}
  body[data-theme="night"] .card-title{{color:#6b7280}}
  body[data-theme="night"] .feed{{background:#1a1d27;border-color:#2d3748}}
  body[data-theme="night"] .ev{{border-color:#2d374840}}
  body[data-theme="night"] .footer{{color:#4b5563}}
  body[data-theme="night"] .input-box{{background:#1a1d27;border-color:#2d3748}}
  body[data-theme="night"] .input-field{{background:#0f1117;border-color:#374151}}
  body[data-theme="night"] .dispatch-field{{background:#0f1117;border-color:#374151}}
  body[data-theme="night"] select{{background:#0f1117;border-color:#374151}}
  body[data-theme="night"] .tool-card{{background:#1a1d27;border-color:#2d3748}}
  body[data-theme="night"] .state-pill{{background:#0f1117;border-color:#374151}}
  body[data-theme="night"] .agent-btn{{background:#0f1117;border-color:#374151}}
  body[data-theme="night"] .theme-btn{{border-color:#374151}}
  body[data-theme="night"] .dispatch-output{{background:#0f1117;border-color:#374151}}
  .grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:1rem}}
  .card{{background:#334155;border:1px solid #64748b;border-radius:4px;padding:1rem}}
  .card-title{{font-size:.75rem;letter-spacing:.1em;text-transform:uppercase;color:#94a3b8;margin-bottom:.5rem}}
  .badge{{display:inline-block;padding:.15rem .5rem;border-radius:2px;font-size:.75rem;margin-bottom:.5rem}}
  .ok{{color:#4ade80}}
  .err{{color:#f87171}}
  .warn{{color:#fbbf24}}
  .url{{color:#38bdf8;font-size:.75rem;font-family:monospace}}
  .role{{color:#94a3b8;font-size:.75rem}}
  .models{{margin-top:.5rem}}
  .model{{color:#cbd5e1;font-size:.75rem;padding:.1rem 0;font-family:monospace}}
  .footer{{margin-top:1.5rem;font-size:.7rem;color:#64748b}}
  .version{{color:#64748b;font-size:.7rem}}
  .section{{margin-top:1.5rem}}
  .section-title{{font-size:.8rem;letter-spacing:.1em;text-transform:uppercase;color:#38bdf8;margin-bottom:.75rem;border-bottom:1px solid #38bdf840;padding-bottom:.25rem}}
  .feed{{background:#334155;border:1px solid #64748b;border-radius:4px;overflow:hidden}}
  .ev{{display:flex;gap:.5rem;padding:.4rem .75rem;border-bottom:1px solid #3f536640;align-items:baseline}}
  .ev:last-child{{border-bottom:none}}
  .ev-ts{{color:#64748b;font-size:.65rem;white-space:nowrap;min-width:5rem;font-family:monospace}}
  .ev-who{{color:#38bdf8;font-size:.7rem;white-space:nowrap;min-width:9rem;font-family:monospace}}
  .ev-tag{{font-size:.65rem;border-radius:2px;padding:.05rem .3rem;white-space:nowrap}}
  .tag-reply{{background:#4ade8020;color:#4ade80}}
  .tag-query{{background:#38bdf820;color:#7dd3fc}}
  .tag-error{{background:#f8717120;color:#f87171}}
  .tag-waiting{{background:#fbbf2420;color:#fbbf24}}
  .tag-user{{background:#a78bfa20;color:#a78bfa}}
  .tag-other{{background:#64748b40;color:#94a3b8}}
  .ev-msg{{color:#cbd5e1;font-size:.75rem;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;flex:1}}
  .none{{color:#64748b;font-size:.75rem;padding:.75rem}}
  /* routing state card */
  .rt-row{{display:flex;gap:.5rem;margin:.2rem 0;font-size:.75rem}}
  .rt-key{{color:#94a3b8;min-width:7rem}}
  .rt-val{{color:#cbd5e1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;flex:1}}
  /* input section */
  .input-section{{margin-top:1.5rem}}
  .input-box{{background:#334155;border:1px solid #64748b;border-radius:4px;padding:1rem}}
  .input-label{{font-size:.75rem;letter-spacing:.1em;text-transform:uppercase;color:#38bdf8;margin-bottom:.75rem;display:block}}
  .input-row{{display:flex;gap:.5rem}}
  .input-field{{flex:1;background:#1e293b;border:1px solid #475569;border-radius:3px;color:#f8fafc;font-family:monospace;font-size:.85rem;padding:.45rem .75rem;outline:none}}
  .input-field:focus{{border-color:#38bdf8}}
  .input-btn{{background:#0369a1;border:none;border-radius:3px;color:#f0f9ff;cursor:pointer;font-family:monospace;font-size:.8rem;padding:.45rem 1rem;white-space:nowrap}}
  .input-btn:hover{{background:#0284c7}}
  .input-status{{font-size:.7rem;color:#64748b;margin-top:.4rem;min-height:1rem}}
  .queue-depth{{font-size:.7rem;color:#fbbf24;margin-top:.3rem}}
  /* agent state pills */
  .agent-states{{margin-top:1rem}}
  .state-pill{{display:inline-flex;align-items:center;gap:.3rem;background:#1e293b;border:1px solid #475569;border-radius:12px;padding:.2rem .6rem;font-size:.7rem;margin:.2rem .2rem 0 0}}
  .s-running{{color:#4ade80}}
  .s-idle{{color:#94a3b8}}
  .s-waiting{{color:#fbbf24}}
  .s-error{{color:#f87171}}
  .s-stopped{{color:#475569}}
  .policy-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:.75rem}}
  .policy-ok{{border-color:#16a34a}}
  .policy-bad{{border-color:#dc2626}}
  .select-row{{display:flex;gap:.5rem;margin-top:.5rem;align-items:center}}
  select{{background:#1e293b;border:1px solid #475569;color:#f8fafc;border-radius:3px;padding:.3rem;font-family:monospace;font-size:.75rem;min-width:12rem}}
  /* tools & apis panel */
  .tools-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:.75rem;margin-top:.5rem}}
  .tool-card{{background:#334155;border:1px solid #475569;border-radius:4px;padding:.75rem}}
  .tool-name{{font-size:.75rem;letter-spacing:.08em;text-transform:uppercase;color:#94a3b8;margin-bottom:.3rem}}
  .tool-hint{{font-size:.65rem;color:#64748b;margin-top:.3rem;line-height:1.4}}
  .tool-hint a{{color:#38bdf8;text-decoration:none}}
  .tool-hint code{{background:#1e293b;border-radius:2px;padding:.05rem .25rem;font-size:.62rem}}
  .tool-cfg{{margin-top:.4rem;display:none}}
  .tool-cfg.open{{display:block}}
  .tool-cfg-row{{display:flex;gap:.4rem;margin-top:.3rem}}
  .tool-cfg-input{{flex:1;background:#1e293b;border:1px solid #475569;border-radius:3px;color:#f8fafc;font-family:monospace;font-size:.75rem;padding:.3rem .5rem;outline:none}}
  .tool-cfg-input:focus{{border-color:#38bdf8}}
  .tool-cfg-save{{background:#0369a1;border:none;border-radius:3px;color:#f0f9ff;cursor:pointer;font-family:monospace;font-size:.7rem;padding:.3rem .6rem;white-space:nowrap}}
  .tool-cfg-save:hover{{background:#0284c7}}
  .tool-cfg-status{{font-size:.65rem;color:#64748b;margin-top:.25rem;min-height:.9rem}}
  .tool-cfg-btn{{background:none;border:1px solid #475569;border-radius:3px;color:#94a3b8;cursor:pointer;font-family:monospace;font-size:.65rem;margin-top:.4rem;padding:.2rem .5rem}}
  .tool-cfg-btn:hover{{border-color:#38bdf8;color:#f8fafc}}
  /* agent dispatch panel */
  .dispatch-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:.5rem;margin-bottom:.75rem}}
  .agent-btn{{background:#1e293b;border:1px solid #475569;border-radius:4px;color:#94a3b8;cursor:pointer;font-family:monospace;font-size:.7rem;padding:.5rem .6rem;text-align:center;transition:border-color .15s,color .15s}}
  .agent-btn:hover{{border-color:#38bdf8;color:#f8fafc}}
  .agent-btn.active{{border-color:#38bdf8;color:#38bdf8;background:#0c2034}}
  .agent-btn.avail::before{{content:"● ";color:#4ade80}}
  .agent-btn.unavail{{opacity:.45;cursor:not-allowed}}
  .agent-btn.unavail::before{{content:"● ";color:#f87171}}
  .dispatch-row{{display:flex;gap:.5rem}}
  .dispatch-field{{flex:1;background:#1e293b;border:1px solid #475569;border-radius:3px;color:#f8fafc;font-family:monospace;font-size:.85rem;padding:.45rem .75rem;outline:none}}
  .dispatch-field:focus{{border-color:#38bdf8}}
  .dispatch-send{{background:#7c3aed;border:none;border-radius:3px;color:#f5f3ff;cursor:pointer;font-family:monospace;font-size:.8rem;padding:.45rem 1rem;white-space:nowrap}}
  .dispatch-send:hover{{background:#6d28d9}}
  .dispatch-status{{font-size:.7rem;color:#64748b;margin-top:.4rem;min-height:1rem}}
  .dispatch-output{{background:#1e293b;border:1px solid #475569;border-radius:3px;color:#a5f3fc;font-family:monospace;font-size:.7rem;margin-top:.5rem;max-height:14rem;overflow-y:auto;padding:.5rem .75rem;white-space:pre-wrap;display:none}}
  /* service-control bar */
  .svc-ctrl{{display:flex;flex-wrap:wrap;gap:.5rem;margin-top:.75rem}}
  .svc-btn{{background:#1e293b;border:1px solid #475569;border-radius:3px;color:#94a3b8;cursor:pointer;font-family:monospace;font-size:.7rem;padding:.35rem .75rem;transition:border-color .15s,color .15s}}
  .svc-btn:hover{{border-color:#38bdf8;color:#f8fafc}}
  .svc-btn.danger{{border-color:#ef4444;color:#f87171}}
  .svc-btn.danger:hover{{background:#7f1d1d;color:#fca5a5}}
  .svc-btn.warn{{border-color:#f59e0b;color:#fbbf24}}
  .svc-btn.warn:hover{{background:#78350f;color:#fde68a}}
  .svc-ctrl-status{{font-size:.7rem;color:#64748b;margin-top:.4rem;min-height:1rem}}
  /* supervisor jobs table */
  .jobs-table{{width:100%;border-collapse:collapse;font-size:.72rem;margin-top:.5rem}}
  .jobs-table th{{color:#64748b;font-weight:600;letter-spacing:.07em;padding:.35rem .6rem;text-align:left;text-transform:uppercase;border-bottom:1px solid #475569}}
  .jobs-table td{{color:#cbd5e1;padding:.3rem .6rem;border-bottom:1px solid #3f536640;font-family:monospace;vertical-align:middle}}
  .jobs-table tr:last-child td{{border-bottom:none}}
  .job-status-queued{{color:#94a3b8}}
  .job-status-running{{color:#4ade80}}
  .job-status-done,.job-status-succeeded{{color:#38bdf8}}
  .job-status-failed{{color:#f87171}}
  .job-status-cancelled{{color:#f59e0b}}
  .job-intent{{color:#a78bfa;font-size:.68rem}}
  .jobs-empty{{color:#64748b;font-size:.75rem;padding:.75rem}}
  body[data-theme="night"] .svc-btn{{background:#0f1117;border-color:#374151}}
  body[data-theme="night"] .jobs-table th{{border-color:#374151}}
  body[data-theme="night"] .jobs-table td{{border-color:#1f2937}}
</style>
</head>
<body>
<nav class="navbar">
  <span class="nav-brand">orama portal</span>
  <div class="nav-links">
    <a class="nav-link" href="/dashboard">Routing Dashboard ↗</a>
    <button class="theme-btn" id="theme-btn" onclick="toggleTheme()">🌙 Night</button>
  </div>
</nav>
<h1>orama portal <span class="version">v{version}</span></h1>
<div id="cards-grid" class="grid">
{cards}
</div>
{service_control_section}
<div id="routing-section">{routing_section}</div>
{hardware_policy_section}
{tools_section}
{agent_dispatch_section}
{supervisor_jobs_section}
{agent_state_section}
<div id="activity-section">{activity_section}</div>
{input_section}
<div class="footer">Auto-refresh every 10s &bull; <span id="last-refresh">{timestamp}</span></div>
<script>
async function sendTask() {{
  const field = document.getElementById('task-input');
  const status = document.getElementById('input-status');
  const msg = field.value.trim();
  if (!msg) {{ status.textContent = 'Enter a task first.'; return; }}
  status.textContent = 'Sending…';
  try {{
    const r = await fetch('/api/user-input', {{
      method: 'POST',
      headers: {{'Content-Type': 'application/json'}},
      body: JSON.stringify({{message: msg}})
    }});
    const d = await r.json();
    if (d.status === 'queued') {{
      status.textContent = '✓ Queued (depth: ' + d.queue_depth + ')';
      field.value = '';
    }} else {{
      status.textContent = 'Error: ' + JSON.stringify(d);
    }}
  }} catch(e) {{
    status.textContent = 'Request failed: ' + e;
  }}
}}
document.addEventListener('DOMContentLoaded', function() {{
  document.getElementById('task-input').addEventListener('keydown', function(e) {{
    if (e.key === 'Enter') sendTask();
  }});
  // Agent dispatch
  let _selectedAgent = 'codex';
  document.querySelectorAll('.agent-btn:not(.unavail)').forEach(btn => {{
    btn.addEventListener('click', function() {{
      document.querySelectorAll('.agent-btn').forEach(b => b.classList.remove('active'));
      this.classList.add('active');
      _selectedAgent = this.dataset.agent;
    }});
  }});
  const firstAvail = document.querySelector('.agent-btn.avail');
  if (firstAvail) {{ firstAvail.classList.add('active'); _selectedAgent = firstAvail.dataset.agent; }}
  document.getElementById('dispatch-field').addEventListener('keydown', function(e) {{
    if (e.key === 'Enter') spawnAgent();
  }});
}});
function toggleCfg(key) {{
  const el = document.getElementById('cfg-' + key);
  if (el) el.classList.toggle('open');
}}
async function saveCfg(tool, envVar) {{
  const input = document.getElementById('cfg-val-' + tool);
  const status = document.getElementById('cfg-status-' + tool);
  const val = input.value.trim();
  if (!val) {{ status.textContent = 'Enter a key first.'; return; }}
  status.textContent = 'Saving…';
  try {{
    const r = await fetch('/api/configure-tool', {{
      method: 'POST',
      headers: {{'Content-Type': 'application/json'}},
      body: JSON.stringify({{tool: tool, env_var: envVar, value: val}})
    }});
    const d = await r.json();
    if (d.ok) {{
      status.textContent = '✓ ' + d.message + ' (page refreshes in 3s)';
      input.value = '';
      setTimeout(() => location.reload(), 3000);
    }} else {{
      status.textContent = '✗ ' + d.message;
    }}
  }} catch(e) {{
    status.textContent = 'Error: ' + e;
  }}
}}
async function spawnAgent() {{
  const field = document.getElementById('dispatch-field');
  const status = document.getElementById('dispatch-status');
  const output = document.getElementById('dispatch-output');
  const task = field.value.trim();
  if (!task) {{ status.textContent = 'Enter a task first.'; return; }}
  status.textContent = 'Dispatching to ' + _selectedAgent + '…';
  output.style.display = 'none';
  try {{
    const r = await fetch('/api/spawn-agent', {{
      method: 'POST',
      headers: {{'Content-Type': 'application/json'}},
      body: JSON.stringify({{agent: _selectedAgent, task: task}})
    }});
    const d = await r.json();
    if (d.ok) {{
      status.textContent = '✓ Done (' + (d.elapsed||'').toFixed(1) + 's)';
      field.value = '';
    }} else {{
      status.textContent = '✗ Agent error';
    }}
    const text = d.output || JSON.stringify(d.results || d, null, 2);
    output.textContent = text;
    output.style.display = 'block';
  }} catch(e) {{
    status.textContent = 'Request failed: ' + e;
  }}
}}
// ── Async data refresh (no page reload) ──────────────────────────────────
async function refreshData() {{
  try {{
    const r = await fetch('/api/status-html');
    if (!r.ok) return;
    const d = await r.json();
    const grid = document.getElementById('cards-grid');
    if (grid && d.cards) grid.innerHTML = d.cards;
    const routing = document.getElementById('routing-section');
    if (routing && d.routing_section) routing.innerHTML = d.routing_section;
    const activity = document.getElementById('activity-section');
    if (activity && d.activity_section) activity.innerHTML = d.activity_section;
    const ts = document.getElementById('last-refresh');
    if (ts && d.timestamp) ts.textContent = d.timestamp;
    if (d.manager_alert) {{
      showToast('⚠ Manager affinity: ' + d.manager_alert, 'warning');
    }}
  }} catch(e) {{
    console.warn('orama portal refresh failed:', e);
  }}
}}
setInterval(refreshData, 10000);
// ── Theme toggle ─────────────────────────────────────────────────────────
function toggleTheme() {{
  const body = document.body;
  const btn = document.getElementById('theme-btn');
  if (body.dataset.theme === 'night') {{
    body.dataset.theme = 'day';
    if (btn) btn.textContent = '🌙 Night';
    localStorage.setItem('orama-theme', 'day');
  }} else {{
    body.dataset.theme = 'night';
    if (btn) btn.textContent = '☀️ Day';
    localStorage.setItem('orama-theme', 'night');
  }}
}}
(function() {{
  const saved = localStorage.getItem('orama-theme');
  if (saved === 'night') {{
    document.body.dataset.theme = 'night';
    const btn = document.getElementById('theme-btn');
    if (btn) btn.textContent = '☀️ Day';
  }}
}})();
function showToast(msg, type) {{
  const t = document.createElement('div');
  t.style.cssText = 'position:fixed;bottom:20px;right:20px;background:' +
    (type==='warning'?'#fff3cd':'#d4edda') + ';color:#333;padding:12px 20px;' +
    'border-radius:6px;box-shadow:0 2px 8px rgba(0,0,0,.2);z-index:9999;' +
    'font-weight:bold;max-width:400px;';
  t.textContent = msg;
  document.body.appendChild(t);
  setTimeout(() => t.remove(), 6000);
}}
// ── Service controls ───────────────────────────────────────────────────────
async function svcAction(action, service) {{
  const statusEl = document.getElementById('svc-ctrl-status');
  if (statusEl) statusEl.textContent = action + (service?' '+service:'') + '…';
  try {{
    const url = action === 'stop' ? '/api/stop' : '/api/restart/' + service;
    const r = await fetch(url, {{method:'POST',headers:{{'Content-Type':'application/json'}},body:'{{}}'}});
    const d = await r.json();
    const msg = d.message || JSON.stringify(d);
    if (statusEl) statusEl.textContent = msg;
    showToast(msg, d.ok ? 'success' : 'warning');
    if (d.ok) setTimeout(refreshData, 2000);
  }} catch(e) {{
    const msg = 'Error: ' + e;
    if (statusEl) statusEl.textContent = msg;
  }}
}}
async function rediscover() {{
  const statusEl = document.getElementById('svc-ctrl-status');
  if (statusEl) statusEl.textContent = 'Re-discovering LAN…';
  try {{
    const r = await fetch('/api/rediscover', {{method:'POST',headers:{{'Content-Type':'application/json'}},body:'{{}}'}});
    const d = await r.json();
    const msg = d.message || JSON.stringify(d);
    if (statusEl) statusEl.textContent = msg;
    showToast(msg, d.ok ? 'success' : 'warning');
    if (d.ok) setTimeout(refreshData, 3000);
  }} catch(e) {{
    if (statusEl) statusEl.textContent = 'Error: ' + e;
  }}
}}
async function recheckPolicy() {{
  const statusEl = document.getElementById('svc-ctrl-status');
  if (statusEl) statusEl.textContent = 'Re-checking hardware policy…';
  try {{
    const r = await fetch('/api/hardware-policy');
    const d = await r.json();
    const ok = d.ok;
    const violations = (d.violations||[]).join(', ');
    const msg = ok ? '✓ Policy clean' : '✗ Violations: ' + (violations||'see panel');
    if (statusEl) statusEl.textContent = msg;
    showToast(msg, ok ? 'success' : 'warning');
  }} catch(e) {{
    if (statusEl) statusEl.textContent = 'Error: ' + e;
  }}
}}
// ── Supervisor jobs refresh ────────────────────────────────────────────────
async function refreshJobs() {{
  const tbody = document.getElementById('jobs-tbody');
  if (!tbody) return;
  try {{
    const r = await fetch('/api/v1/jobs');
    if (!r.ok) return;
    const jobs = await r.json();
    if (!jobs.length) {{
      tbody.innerHTML = '<tr><td colspan="5" class="jobs-empty">No jobs yet</td></tr>';
      return;
    }}
    tbody.innerHTML = jobs.slice(0,20).map(j => {{
      const cls = 'job-status-' + (j.status||'unknown');
      const ts = j.created_at ? new Date(j.created_at*1000).toLocaleTimeString() : '';
      const elapsed = j.elapsed_s != null ? j.elapsed_s.toFixed(1)+'s' : '';
      return '<tr>' +
        '<td><span class="job-intent">' + _esc(j.intent||'') + '</span></td>' +
        '<td><span class="'+cls+'">' + _esc(j.status||'') + '</span></td>' +
        '<td>' + _esc(j.backend||'') + '</td>' +
        '<td>' + ts + '</td>' +
        '<td>' + elapsed + '</td>' +
        '</tr>';
    }}).join('');
  }} catch(e) {{ /* silent */ }}
}}
function _esc(s) {{
  return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}}
setInterval(refreshJobs, 8000);
setTimeout(refreshJobs, 1000);
</script>
</body>
</html>"""


def _status_badge(ok: bool) -> str:
    if ok:
        return '<span class="ok">&#9679; ONLINE</span>'
    return '<span class="err">&#9679; OFFLINE</span>'


def _render_card(title: str, ok: bool, url: str, role: str = "", models: List[str] = None, extra: str = "") -> str:
    models_html = ""
    if models:
        items = "".join(f'<div class="model">&rsaquo; {m}</div>' for m in models[:5])
        if len(models) > 5:
            items += f'<div class="model">...+{len(models)-5} more</div>'
        models_html = f'<div class="models">{items}</div>'
    role_html = f'<div class="role">{role}</div>' if role else ""
    return (
        f'<div class="card">'
        f'<div class="card-title">{title}</div>'
        f'{_status_badge(ok)}'
        f'{role_html}'
        f'<div class="url">{url}</div>'
        f'{models_html}'
        f'{extra}'
        f'</div>'
    )


def _render_tools_section(tools: Dict[str, Any]) -> str:
    """Render a full Tools & APIs panel — all AlphaClaw + PT keys, grouped, with inline config."""

    GROUP_ORDER = ["ai", "tools", "channels", "github", "cli", "gateway"]
    GROUP_LABELS = {
        "ai": "AI Providers",
        "tools": "Search & Tools",
        "channels": "Messaging Channels",
        "github": "GitHub",
        "cli": "CLI Tools",
        "gateway": "Gateways",
    }

    def _tool_card(key: str, name: str, ok: bool, detail: str,
                   env_var: str = "", hint_link: str = "",
                   key_present: bool = False) -> str:
        """
        ok          = True  → READY (green, no configure button)
        ok          = False, key_present = False → NOT CONFIGURED (amber, configure button)
        ok          = False, key_present = True  → KEY SET BUT FAILING (red, replace button)
        """
        if ok:
            badge = '<span class="ok">&#9679; READY</span>'
            cfg_html = ""
        elif key_present:
            badge = '<span class="err">&#9679; KEY SET BUT FAILING</span>'
            # Allow re-entering the key
            cfg_html = ""
            if env_var:
                link_html = f' <a href="{hint_link}" target="_blank">Get key &#8599;</a>' if hint_link else ""
                cfg_html = (
                    f'<button class="tool-cfg-btn" onclick="toggleCfg(\'{key}\')">'
                    f'&#x21ba; Replace key{link_html}</button>'
                    f'<div class="tool-cfg" id="cfg-{key}">'
                    f'<div class="tool-cfg-row">'
                    f'<input class="tool-cfg-input" id="cfg-val-{key}" type="password" '
                    f'placeholder="new {env_var}..." autocomplete="off" />'
                    f'<button class="tool-cfg-save" onclick="saveCfg(\'{key}\',\'{env_var}\')">Save</button>'
                    f'</div>'
                    f'<div class="tool-cfg-status" id="cfg-status-{key}"></div>'
                    f'</div>'
                )
        else:
            badge = '<span class="warn">&#9679; NOT CONFIGURED</span>'
            cfg_html = ""
            if env_var:
                link_html = f' <a href="{hint_link}" target="_blank">Get key &#8599;</a>' if hint_link else ""
                cfg_html = (
                    f'<button class="tool-cfg-btn" onclick="toggleCfg(\'{key}\')">'
                    f'&#x2699; Configure{link_html}</button>'
                    f'<div class="tool-cfg" id="cfg-{key}">'
                    f'<div class="tool-cfg-row">'
                    f'<input class="tool-cfg-input" id="cfg-val-{key}" type="password" '
                    f'placeholder="{env_var}=..." autocomplete="off" />'
                    f'<button class="tool-cfg-save" onclick="saveCfg(\'{key}\',\'{env_var}\')">Save</button>'
                    f'</div>'
                    f'<div class="tool-cfg-status" id="cfg-status-{key}"></div>'
                    f'</div>'
                )
        return (
            f'<div class="tool-card">'
            f'<div class="tool-name">{name}</div>'
            f'{badge}'
            f'<div class="tool-hint" style="margin-top:.25rem">{detail}</div>'
            f'{cfg_html}'
            f'</div>'
        )

    # Build hint_link lookup from _ALL_KNOWN_KEYS
    _hint_map = {env_var: link for env_var, _, _, link in _ALL_KNOWN_KEYS}

    # Group tools by their "group" field
    grouped: Dict[str, List] = {g: [] for g in GROUP_ORDER}
    for slug, entry in tools.items():
        g = entry.get("group", "tools")
        if g not in grouped:
            grouped[g] = []
        grouped[g].append((slug, entry))

    sections_html = []
    for group in GROUP_ORDER:
        entries = grouped.get(group, [])
        if not entries:
            continue
        cards = []
        for slug, entry in entries:
            env_var = entry.get("env_var", "")
            hint_link = _hint_map.get(env_var, "")
            cards.append(_tool_card(
                slug,
                entry.get("label", slug),
                entry.get("ok", False),
                detail=entry.get("detail", ""),
                env_var=env_var,
                hint_link=hint_link,
                key_present=entry.get("key_present", False),
            ))
        glabel = GROUP_LABELS.get(group, group.title())
        sections_html.append(
            f'<div class="section-title" style="font-size:.7rem;margin-top:.75rem">{glabel}</div>'
            f'<div class="tools-grid">{"".join(cards)}</div>'
        )

    return (
        '<div class="section">'
        '<div class="section-title">Tools &amp; APIs</div>'
        + "".join(sections_html)
        + '</div>'
    )


def _ollama_mac_busy_flag(svc: Dict[str, Any]) -> bool:
    """True when Ollama has a model loaded in VRAM (actively running inference)."""
    return bool(svc.get("ollama_mac", {}).get("busy", False))


def _lmstudio_mac_busy_flag(agents: List[Dict[str, Any]]) -> bool:
    """True when any running agent is dispatched to the Mac LM Studio backend."""
    for a in agents:
        if a.get("status") == "running":
            backend = (a.get("backend") or a.get("coder_backend") or "").lower()
            if "lmstudio" in backend or "lms-mac" in backend or "lmstudio-mac" in backend:
                return True
    return False


def _render_agent_dispatch_section(agent_availability: Dict[str, bool]) -> str:
    """Render the Agent Dispatch panel with live availability badges."""
    AGENTS = [
        ("codex",         "Codex",              "CLI · local"),
        ("gemini-review", "Gemini Review",       "CLI · code review"),
        ("gemini",        "Gemini CLI",          "CLI · local"),
        ("ollama-mac",    "Ollama Mac",          "HTTP · localhost:11434"),
        ("lmstudio-mac",  "LM Studio Mac",       "HTTP · localhost"),
        ("lmstudio-win",  "LM Studio Win",       f"HTTP · .{_get_win_ip().split('.')[-1]} GPU"),
        ("all",           "All (parallel)",      "Codex + Gemini + Mac; Win serial"),
    ]
    btns = []
    for key, label, hint in AGENTS:
        if key == "all":
            css = "avail"  # always show "all" as available
        else:
            css = "avail" if agent_availability.get(key) else "unavail"
        btns.append(
            f'<button class="agent-btn {css}" data-agent="{key}" title="{hint}">'
            f'{label}<br><span style="font-size:.6rem;color:#64748b">{hint}</span>'
            f'</button>'
        )
    return (
        '<div class="section">'
        '<div class="section-title">Agent Dispatch</div>'
        '<div class="input-box">'
        '<span class="input-label">Select agent, enter task, press Enter or Send</span>'
        '<div class="dispatch-grid">' + "".join(btns) + '</div>'
        '<div class="dispatch-row">'
        '<input class="dispatch-field" id="dispatch-field" type="text" placeholder="Task for selected agent…" />'
        '<button class="dispatch-send" onclick="spawnAgent()">Send</button>'
        '</div>'
        '<div class="dispatch-status" id="dispatch-status"></div>'
        '<pre class="dispatch-output" id="dispatch-output"></pre>'
        '</div>'
        '</div>'
    )


def _render_routing_section(routing: Dict[str, Any] | None) -> str:
    if not routing:
        return (
            '<div class="section">'
            '<div class="section-title">Routing State</div>'
            '<div class="feed"><div class="none">Routing state unavailable — PT may still be probing backends</div></div>'
            '</div>'
        )
    distributed = routing.get("distributed", False)
    mode_color = "ok" if distributed else "warn"
    mode_text = "DISTRIBUTED" if distributed else "SINGLE"
    rows = [
        f'<div class="rt-row"><span class="rt-key">mode</span><span class="rt-val {mode_color}">{mode_text}</span></div>',
        f'<div class="rt-row"><span class="rt-key">manager</span><span class="rt-val">{routing.get("manager_endpoint","—")}</span></div>',
        f'<div class="rt-row"><span class="rt-key">manager model</span><span class="rt-val">{routing.get("manager_model","—")}</span></div>',
        f'<div class="rt-row"><span class="rt-key">coder</span><span class="rt-val">{routing.get("coder_endpoint","—")}</span></div>',
        f'<div class="rt-row"><span class="rt-key">coder model</span><span class="rt-val">{routing.get("coder_model","—")}</span></div>',
        f'<div class="rt-row"><span class="rt-key">mac reachable</span><span class="rt-val">{"✓" if routing.get("mac_reachable") else "✗"}</span></div>',
        f'<div class="rt-row"><span class="rt-key">win reachable</span><span class="rt-val">{"✓" if routing.get("lmstudio_detected") else "✗"}</span></div>',
    ]
    synced_at = routing.get("synced_at", "")
    if synced_at:
        rows.append(f'<div class="rt-row"><span class="rt-key">synced at</span><span class="rt-val">{synced_at}</span></div>')
    alert = routing.get("manager_affinity_alert")
    if alert:
        rows.append(
            f'<div class="rt-row" style="background:#fff3cd;color:#856404;font-weight:bold;padding:6px 10px;">'
            f'⚠ Manager affinity violation: {_html.escape(str(alert))}</div>'
        )
    return (
        '<div class="section">'
        '<div class="section-title">Routing State</div>'
        '<div class="card">' + "".join(rows) + '</div>'
        '</div>'
    )


def _render_hardware_policy_section(policy_status: Dict[str, Any] | None) -> str:
    if not policy_status:
        return (
            '<div class="section"><div class="section-title">Hardware Policy</div>'
            '<div class="feed"><div class="none">Hardware policy unavailable</div></div></div>'
        )
    violations = policy_status.get("violations", [])
    ok = not violations
    badge = '<span class="ok">● CLEAN</span>' if ok else '<span class="err">● VIOLATIONS</span>'
    policy = policy_status.get("policy", {})
    live = policy_status.get("live", {})
    safe = policy_status.get("safe_defaults", {})

    def _items(values: list[str]) -> str:
        return "".join(f'<div class="model">› {v}</div>' for v in values) or '<div class="none">none</div>'

    mac_opts = "".join(f'<option>{m}</option>' for m in safe.get("mac", []))
    win_opts = "".join(f'<option>{m}</option>' for m in safe.get("win", []))
    violations_html = "".join(f'<div class="model err">✗ {v}</div>' for v in violations)
    if not violations_html:
        violations_html = '<div class="model ok">✓ no forbidden assignments found</div>'

    return (
        '<div class="section"><div class="section-title">Hardware Policy & Safe Defaults</div>'
        '<div class="policy-grid">'
        f'<div class="card {"policy-ok" if ok else "policy-bad"}"><div class="card-title">Policy Status</div>{badge}'
        f'<div class="role">source: {policy_status.get("policy_path", "—")}</div>{violations_html}</div>'
        '<div class="card"><div class="card-title">Mac Safe Models (NEVER_WIN)</div>'
        f'{_items(live.get("mac_allowed", []))}'
        f'<div class="select-row"><span class="role">choose:</span><select>{mac_opts}</select></div></div>'
        '<div class="card"><div class="card-title">Win Safe Models (NEVER_MAC)</div>'
        f'{_items(live.get("win_allowed", []))}'
        f'<div class="select-row"><span class="role">choose:</span><select>{win_opts}</select></div></div>'
        '<div class="card"><div class="card-title">Policy Lists</div>'
        f'<div class="role">NEVER_MAC</div>{_items(policy.get("windows_only", [])[:4])}'
        f'<div class="role" style="margin-top:.5rem">NEVER_WIN</div>{_items(policy.get("mac_only", [])[:4])}'
        '<div class="role" style="margin-top:.5rem">CLI: ./start.sh --hardware-policy</div></div>'
        '</div></div>'
    )


def _render_agent_state_section(agents: List[Dict[str, Any]]) -> str:
    if not agents:
        return (
            '<div class="section">'
            '<div class="section-title">Active Agents</div>'
            '<div class="feed"><div class="none">No agents registered yet</div></div>'
            '</div>'
        )
    pills = []
    for a in agents:
        status = a.get("status", "unknown")
        role = a.get("role", a.get("agent_id", "?"))
        model = a.get("model", "")
        css = {"running": "s-running", "idle": "s-idle", "error": "s-error",
               "stopped": "s-stopped", "waiting_for_input": "s-waiting"}.get(status, "s-idle")
        icon = {"running": "▶", "idle": "◉", "error": "✗",
                "stopped": "◻", "waiting_for_input": "✋"}.get(status, "·")
        label = f"{icon} {role}"
        if model:
            label += f"  <span style='color:#64748b'>{model[:30]}</span>"
        pills.append(f'<span class="state-pill"><span class="{css}">{label}</span></span>')
    return (
        '<div class="section">'
        '<div class="section-title">Active Agents</div>'
        '<div class="agent-states">' + "".join(pills) + '</div>'
        '</div>'
    )


def _render_activity_section(events: List[Dict[str, Any]]) -> str:
    import datetime

    def _fmt_ts(ts: float) -> str:
        try:
            return datetime.datetime.fromtimestamp(ts).strftime("%H:%M:%S")
        except Exception:
            return "—"

    def _tag(event: str) -> str:
        if event in ("reply", "reply_received"):
            return '<span class="ev-tag tag-reply">reply</span>'
        if event in ("query_sent", "started"):
            return '<span class="ev-tag tag-query">{}</span>'.format(event)
        if event == "error":
            return '<span class="ev-tag tag-error">error</span>'
        if event in ("waiting_for_input",):
            return '<span class="ev-tag tag-waiting">waiting</span>'
        if event in ("user_task_received",):
            return '<span class="ev-tag tag-user">user task</span>'
        return '<span class="ev-tag tag-other">{}</span>'.format(event)

    if not events:
        return (
            '<div class="section">'
            '<div class="section-title">Autoresearchers</div>'
            '<div class="feed"><div class="none">No activity yet — run scripts/launch_researchers.py</div></div>'
            '</div>'
        )

    rows = []
    for ev in events[:15]:
        msg = ev.get("msg", "")[:120].replace("<", "&lt;").replace(">", "&gt;")
        rows.append(
            '<div class="ev">'
            f'<span class="ev-ts">{_fmt_ts(ev.get("ts", 0))}</span>'
            f'<span class="ev-who">{ev.get("agent","?")}</span>'
            f'{_tag(ev.get("event","?"))}'
            f'<span class="ev-msg">{msg}</span>'
            '</div>'
        )
    return (
        '<div class="section">'
        '<div class="section-title">Autoresearchers</div>'
        '<div class="feed">'
        + "".join(rows)
        + '</div></div>'
    )


def _render_input_section(queue_depth: int) -> str:
    depth_html = ""
    if queue_depth > 0:
        depth_html = f'<div class="queue-depth">&#9679; {queue_depth} task(s) pending in queue</div>'
    return (
        '<div class="input-section">'
        '<div class="input-box">'
        '<label class="input-label" for="task-input">Send Task to Agents</label>'
        '<div class="input-row">'
        '<input id="task-input" class="input-field" type="text" '
        'placeholder="Describe the task for the researchers…" autocomplete="off">'
        '<button class="input-btn" onclick="sendTask()">Send &#9654;</button>'
        '</div>'
        f'<div class="input-status" id="input-status">{depth_html}</div>'
        '<div style="font-size:.65rem;color:#475569;margin-top:.4rem">'
        f'CLI: curl -sX POST {PT_URL}/user-input -H \'Content-Type: application/json\' '
        '-d \'{"message":"your task"}\''
        '</div>'
        '</div>'
        '</div>'
    )


def _render_service_control_section() -> str:
    """Service-control bar: Stop All, per-service Restart, Re-discover LAN, Re-check Policy."""
    return (
        '<div class="section">'
        '<div class="section-title">Service Controls</div>'
        '<div class="card">'
        '<div class="svc-ctrl">'
        '<button class="svc-btn danger" onclick="svcAction(\'stop\')">&#9632; Stop All</button>'
        '<button class="svc-btn warn" onclick="svcAction(\'restart\',\'pt\')">&#8635; Restart PT :8000</button>'
        '<button class="svc-btn warn" onclick="svcAction(\'restart\',\'orama\')">&#8635; Restart orama :8001</button>'
        '<button class="svc-btn warn" onclick="svcAction(\'restart\',\'portal\')">&#8635; Restart Portal :8002</button>'
        '<button class="svc-btn" onclick="rediscover()">&#8635; Re-discover LAN</button>'
        '<button class="svc-btn" onclick="recheckPolicy()">&#10003; Re-check Policy</button>'
        '</div>'
        '<div class="svc-ctrl-status" id="svc-ctrl-status"></div>'
        '<div style="font-size:.65rem;color:#475569;margin-top:.4rem">'
        'CLI: ./start.sh --stop &bull; ./start.sh --discover &bull; ./start.sh --hardware-policy'
        '</div>'
        '</div>'
        '</div>'
    )


def _render_supervisor_jobs_section(jobs: List[Dict[str, Any]]) -> str:
    """V1 OrchestrationSupervisor jobs panel — polls PT /v1/jobs."""
    if not jobs:
        rows_html = '<tr><td colspan="5" class="jobs-empty">No supervisor jobs yet — submit via PT API or agent dispatch</td></tr>'
    else:
        def _esc(s: str) -> str:
            return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

        row_parts = []
        import datetime as _dt
        for j in jobs[:20]:
            status = j.get("status", "unknown")
            cls = f"job-status-{status}"
            ts_raw = j.get("created_at", 0)
            try:
                ts_str = _dt.datetime.fromtimestamp(float(ts_raw)).strftime("%H:%M:%S") if ts_raw else "—"
            except Exception:
                ts_str = "—"
            elapsed = j.get("elapsed_s")
            elapsed_str = f"{float(elapsed):.1f}s" if elapsed is not None else "—"
            row_parts.append(
                "<tr>"
                f'<td><span class="job-intent">{_esc(j.get("intent",""))}</span></td>'
                f'<td><span class="{cls}">{_esc(status)}</span></td>'
                f'<td>{_esc(j.get("backend",""))}</td>'
                f'<td>{ts_str}</td>'
                f'<td>{elapsed_str}</td>'
                "</tr>"
            )
        rows_html = "".join(row_parts)

    return (
        '<div class="section">'
        '<div class="section-title">Supervisor Jobs (PT /v1/jobs)</div>'
        '<div class="card">'
        '<table class="jobs-table">'
        '<thead><tr>'
        '<th>Intent</th><th>Status</th><th>Backend</th><th>Created</th><th>Elapsed</th>'
        '</tr></thead>'
        f'<tbody id="jobs-tbody">{rows_html}</tbody>'
        '</table>'
        '</div>'
        '</div>'
    )


def _render_html(status: Dict[str, Any]) -> str:
    import datetime

    cards = []
    svc = status.get("services", {})

    # PT
    pt = svc.get("perplexity_tools", {})
    cards.append(_render_card(
        "Perpetua-Tools", pt.get("ok", False), pt.get("url", ""),
        role="orchestrator / cloud router",
        extra=f'<div class="version">{pt.get("version","")}</div>',
    ))

    # US
    us = svc.get("ultrathink", {})
    cards.append(_render_card(
        "orama API", us.get("ok", False), us.get("url", ""),
        role="5-stage reasoning bridge",
        extra=f'<div class="version">{us.get("version","")}</div>',
    ))

    # LM Studio Mac
    lm_mac = svc.get("lmstudio_mac", {})
    cards.append(_render_card(
        "LM Studio — Mac", lm_mac.get("ok", False), lm_mac.get("url", ""),
        role="orchestrator + validator + presenter",
        models=lm_mac.get("models", []),
    ))

    # LM Studio Win(s)
    for key, entry in svc.items():
        if key.startswith("lmstudio_win"):
            label = "LM Studio — Win" if key == "lmstudio_win" else f"LM Studio — {key}"
            cards.append(_render_card(
                label, entry.get("ok", False), entry.get("url", ""),
                role="UltraThink agent (coder/checker/refiner/executor/verifier)",
                models=entry.get("models", []),
            ))

    # Ollama Win
    ol_win = svc.get("ollama_win", {})
    cards.append(_render_card(
        "Ollama — Win (fallback)", ol_win.get("ok", False), ol_win.get("url", ""),
        models=ol_win.get("models", []),
    ))

    # Ollama Mac
    ol_mac = svc.get("ollama_mac", {})
    cards.append(_render_card(
        "Ollama — Mac (manager)", ol_mac.get("ok", False), ol_mac.get("url", ""),
        role="manager: qwen3.5:9b-nvfp4",
        models=ol_mac.get("models", []),
    ))

    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    activity_events = status.get("activity", [])
    routing = status.get("routing")
    agents = status.get("agents", [])
    queue_depth = status.get("queue_depth", 0)
    hardware_policy = status.get("hardware_policy")
    tools = status.get("tools", {})
    # Agent dispatch availability — derived from service probes + tool probes
    svc = status.get("services", {})
    _ollama_busy = _ollama_mac_busy_flag(svc)
    _lmstudio_busy = _lmstudio_mac_busy_flag(agents)
    agent_availability = {
        "ollama-mac":     svc.get("ollama_mac", {}).get("ok", False) and not _lmstudio_busy,
        "lmstudio-mac":   svc.get("lmstudio_mac", {}).get("ok", False) and not _ollama_busy,
        "lmstudio-win": (
            svc.get("lmstudio_win", {}).get("ok", False)
            or any(v.get("ok") for k, v in svc.items() if k.startswith("lmstudio_win_"))
        ),
        "codex":          tools.get("codex-cli", {}).get("ok", False),
        "gemini":         tools.get("gemini-cli", {}).get("ok", False),
        "gemini-review":  tools.get("gemini-cli", {}).get("ok", False),
        "ollama_mac_busy":   _ollama_busy,
        "lmstudio_mac_busy": _lmstudio_busy,
    }
    jobs = status.get("supervisor_jobs", [])
    return HTML_TEMPLATE.format(
        version=VERSION,
        cards="\n".join(cards),
        service_control_section=_render_service_control_section(),
        routing_section=_render_routing_section(routing),
        hardware_policy_section=_render_hardware_policy_section(hardware_policy),
        tools_section=_render_tools_section(tools),
        agent_dispatch_section=_render_agent_dispatch_section(agent_availability),
        supervisor_jobs_section=_render_supervisor_jobs_section(jobs),
        agent_state_section=_render_agent_state_section(agents),
        activity_section=_render_activity_section(activity_events),
        input_section=_render_input_section(queue_depth),
        timestamp=ts,
    )


# ── Probes ─────────────────────────────────────────────────────────────────────

async def _probe_http(client: httpx.AsyncClient, url: str) -> tuple[bool, str]:
    try:
        r = await client.get(url, timeout=PROBE_TIMEOUT)
        version = ""
        try:
            data = r.json()
            version = data.get("version", "")
        except Exception:
            pass
        return r.status_code < 500, version
    except Exception:
        return False, ""


async def _probe_lms_models(client: httpx.AsyncClient, endpoint: str, token: str) -> tuple[bool, List[str]]:
    try:
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        r = await client.get(f"{endpoint}/v1/models", headers=headers, timeout=PROBE_TIMEOUT)
        r.raise_for_status()
        models = [m["id"] for m in r.json().get("data", [])]
        return True, models
    except Exception:
        return False, []


async def _probe_ollama_models(client: httpx.AsyncClient, endpoint: str) -> tuple[bool, List[str]]:
    try:
        r = await client.get(f"{endpoint}/api/tags", timeout=PROBE_TIMEOUT)
        r.raise_for_status()
        models = [m.get("name", "") for m in r.json().get("models", [])]
        return True, models
    except Exception:
        return False, []


async def _probe_ollama_ps(client: httpx.AsyncClient, endpoint: str) -> bool:
    """Return True if Ollama has at least one model loaded in VRAM (actively busy)."""
    try:
        r = await client.get(f"{endpoint}/api/ps", timeout=PROBE_TIMEOUT)
        r.raise_for_status()
        return bool(r.json().get("models"))
    except Exception:
        return False


async def _probe_activity(client: httpx.AsyncClient) -> List[Dict[str, Any]]:
    try:
        r = await client.get(f"{PT_URL}/activity?limit=15", timeout=PROBE_TIMEOUT)
        r.raise_for_status()
        return r.json().get("events", [])
    except Exception:
        return []


async def _probe_agents(client: httpx.AsyncClient) -> List[Dict[str, Any]]:
    """Fetch active agents from PT's /agents endpoint."""
    try:
        r = await client.get(f"{PT_URL}/agents", timeout=PROBE_TIMEOUT)
        r.raise_for_status()
        return r.json().get("agents", [])
    except Exception:
        return []


async def _probe_routing(client: httpx.AsyncClient) -> Dict[str, Any] | None:
    """Fetch current routing state from PT's /runtime endpoint."""
    try:
        r = await client.get(f"{PT_URL}/runtime", timeout=PROBE_TIMEOUT)
        r.raise_for_status()
        return r.json()
    except Exception:
        return None


async def _probe_queue_depth(client: httpx.AsyncClient) -> int:
    """Fetch pending user-input queue depth from PT."""
    try:
        r = await client.get(f"{PT_URL}/user-input/status", timeout=PROBE_TIMEOUT)
        r.raise_for_status()
        return r.json().get("queue_depth", 0)
    except Exception:
        return 0


async def _probe_supervisor_jobs(client: httpx.AsyncClient) -> List[Dict[str, Any]]:
    """Fetch V1 supervisor job list from PT /v1/jobs (latest 20, all statuses)."""
    try:
        r = await client.get(f"{PT_URL}/v1/jobs", timeout=PROBE_TIMEOUT)
        r.raise_for_status()
        data = r.json()
        # PT returns list directly or {jobs: [...]}
        if isinstance(data, list):
            return data
        return data.get("jobs", [])
    except Exception:
        return []


def _simple_policy_parse(text: str) -> Dict[str, List[str]]:
    parsed: Dict[str, List[str]] = {"windows_only": [], "mac_only": [], "shared": []}
    current: str | None = None
    for raw_line in text.splitlines():
        line = raw_line.split("#", 1)[0].rstrip()
        if not line.strip():
            continue
        stripped = line.strip()
        if stripped.endswith(":") and not stripped.startswith("-"):
            key = stripped[:-1]
            current = key if key in parsed else None
            continue
        if current and stripped.startswith("-"):
            value = stripped[1:].strip().strip('"').strip("'")
            if value:
                parsed[current].append(value)
    return parsed


def _load_hardware_policy() -> tuple[Dict[str, List[str]], str]:
    policy_path = PERPETUA_TOOLS_ROOT / "config" / "model_hardware_policy.yml"
    if not policy_path.exists():
        return {"windows_only": [], "mac_only": [], "shared": []}, str(policy_path)
    return _simple_policy_parse(policy_path.read_text(encoding="utf-8")), str(policy_path)


def _hardware_policy_status(services: Dict[str, Any]) -> Dict[str, Any]:
    policy, policy_path = _load_hardware_policy()
    win_only = {m.lower() for m in policy.get("windows_only", [])}
    mac_only = {m.lower() for m in policy.get("mac_only", [])}
    mac_models = services.get("lmstudio_mac", {}).get("models", []) or []
    win_models: List[str] = []
    for key, svc in services.items():
        if key.startswith("lmstudio_win"):
            win_models.extend(svc.get("models", []) or [])

    violations = [f"NEVER_MAC {m} advertised by lmstudio-mac" for m in mac_models if m.lower() in win_only]
    violations.extend(f"NEVER_WIN {m} advertised by lmstudio-win" for m in win_models if m.lower() in mac_only)
    mac_allowed = [m for m in mac_models if m.lower() not in win_only and "embed" not in m.lower()]
    win_allowed = [m for m in win_models if m.lower() not in mac_only and "embed" not in m.lower()]
    return {
        "ok": not violations,
        "policy_path": policy_path,
        "policy": policy,
        "violations": violations,
        "live": {"mac_allowed": mac_allowed, "win_allowed": win_allowed},
        "safe_defaults": {
            "mac": mac_allowed or [m for m in policy.get("mac_only", []) if m],
            "win": win_allowed or [m for m in policy.get("windows_only", []) if m],
        },
    }


# ── Routes ─────────────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {"status": "ok", "version": VERSION}


class UserInputRequest(BaseModel):
    message: str
    source: str = "portal"


class AppStateSection(BaseModel):
    """Portal DTO only; Perpetua-Tools remains the durable runtime/job owner."""

    available: bool
    data: Any = None
    error: Optional[str] = None
    source: str


async def _fetch_pt_section(
    client: httpx.AsyncClient,
    path: str,
    *,
    source: str,
    default: Any,
) -> AppStateSection:
    try:
        r = await client.get(f"{PT_URL}{path}", timeout=PROBE_TIMEOUT)
        r.raise_for_status()
        return AppStateSection(available=True, data=r.json(), source=source)
    except Exception as exc:
        return AppStateSection(
            available=False,
            data=default,
            error=str(exc),
            source=source,
        )


def _normalize_jobs_payload(payload: Any) -> List[Dict[str, Any]]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict):
        jobs = payload.get("jobs", [])
        if isinstance(jobs, list):
            return [item for item in jobs if isinstance(item, dict)]
    return []


def _dump_model(model: BaseModel) -> Dict[str, Any]:
    dump = getattr(model, "model_dump", None)
    if callable(dump):
        return dump()
    return model.dict()


class SwarmPreviewRequest(BaseModel):
    objective: str
    task_type: str = "implementation"
    optimize_for: str = "reliability"
    preferred_device: str = "auto"


class SwarmLaunchRequest(SwarmPreviewRequest):
    approved: bool = False


_SWARM_PREVIEW_ROLES = [
    {
        "role": "context-agent",
        "specialization": "codebase-map",
        "intent": "Map relevant files, contracts, risks, and existing patterns.",
        "expected_output_shape": "compact_context_brief",
        "verification_rubric": "Cites concrete files and distinguishes facts from assumptions.",
    },
    {
        "role": "architect-agent",
        "specialization": "implementation-design",
        "intent": "Turn the objective into a bounded implementation plan.",
        "expected_output_shape": "implementation_plan",
        "verification_rubric": "Plan preserves repo boundaries and identifies contract risks.",
    },
    {
        "role": "executor-agent",
        "specialization": "code-change",
        "intent": "Apply the approved implementation in the smallest safe patch.",
        "expected_output_shape": "patch_summary",
        "verification_rubric": "Patch is scoped, tested, and avoids durable state drift.",
    },
    {
        "role": "verifier-agent",
        "specialization": "test-and-review",
        "intent": "Run focused tests and inspect behavioral regressions.",
        "expected_output_shape": "verification_report",
        "verification_rubric": "Reports exact commands, pass/fail state, and remaining risk.",
    },
    {
        "role": "crystallizer-agent",
        "specialization": "artifact-summary",
        "intent": "Summarize outcomes, decisions, and follow-up artifacts.",
        "expected_output_shape": "operator_brief",
        "verification_rubric": "Contains no raw transcripts and links only safe artifacts.",
    },
]


async def _route_preview_assignment(
    client: httpx.AsyncClient,
    *,
    objective: str,
    task_type: str,
    role: str,
    preferred_device: str,
) -> Dict[str, Any]:
    try:
        r = await client.post(
            f"{PT_URL}/models/route",
            json={
                "objective": objective,
                "task_type": task_type,
                "role": role,
                "preferred_device": preferred_device,
            },
            timeout=PROBE_TIMEOUT,
        )
        r.raise_for_status()
        data = r.json()
        return {
            "backend_hint": data.get("backend_hint") or data.get("backend") or data.get("provider") or "auto",
            "model_hint": data.get("model_hint") or data.get("model") or data.get("model_id"),
            "routing_source": "pt:/models/route",
        }
    except Exception:
        return {}


def _fallback_backend_hint(role: str, hardware_policy: Dict[str, Any]) -> str:
    safe_defaults = hardware_policy.get("safe_defaults", {}) if isinstance(hardware_policy, dict) else {}
    if role in {"context-agent", "architect-agent"} and safe_defaults.get("win"):
        return "lmstudio-win"
    if safe_defaults.get("mac"):
        return "lmstudio-mac"
    if safe_defaults.get("win"):
        return "lmstudio-win"
    return "auto"


async def _build_swarm_preview(req: SwarmPreviewRequest) -> Dict[str, Any]:
    objective = req.objective.strip()
    if not objective:
        raise HTTPException(status_code=422, detail="objective is required")
    if len(objective) > 4000:
        raise HTTPException(status_code=422, detail="objective is too long")

    portal_status = await api_status()
    hardware_policy = portal_status.get("hardware_policy", {})

    async with httpx.AsyncClient(timeout=PROBE_TIMEOUT) as client:
        routed = await asyncio.gather(
            *[
                _route_preview_assignment(
                    client,
                    objective=objective,
                    task_type=req.task_type,
                    role=item["role"],
                    preferred_device=req.preferred_device,
                )
                for item in _SWARM_PREVIEW_ROLES
            ]
        )

    assignments = []
    for base, route in zip(_SWARM_PREVIEW_ROLES, routed):
        backend_hint = route.get("backend_hint") or _fallback_backend_hint(base["role"], hardware_policy)
        assignments.append({
            **base,
            "backend_hint": backend_hint,
            "model_hint": route.get("model_hint"),
            "routing_source": route.get("routing_source") or "portal:fallback",
            "dispatch_allowed": False,
        })

    return {
        "objective": objective,
        "task_type": req.task_type,
        "optimize_for": req.optimize_for,
        "preferred_device": req.preferred_device,
        "dispatch_allowed": False,
        "routing_source": (
            "pt:/models/route"
            if any(item["routing_source"] == "pt:/models/route" for item in assignments)
            else "portal:fallback"
        ),
        "hardware_policy": hardware_policy,
        "assignments": assignments,
    }


def _extract_pt_job_id(payload: Any) -> Optional[str]:
    if isinstance(payload, dict):
        for key in ("job_id", "id"):
            value = payload.get(key)
            if value:
                return str(value)
        job = payload.get("job")
        if isinstance(job, dict):
            return _extract_pt_job_id(job)
    return None


_RAW_ARTIFACT_FIELDS = {
    "raw_transcript",
    "transcript",
    "raw_prompt",
    "prompt",
    "tool_trace",
    "tool_traces",
    "messages",
    "model_internals",
    "chain_of_thought",
}


def _collect_redacted_fields(value: Any, prefix: str = "") -> List[str]:
    redacted: List[str] = []
    if isinstance(value, dict):
        for key, nested in value.items():
            path = f"{prefix}.{key}" if prefix else key
            if key in _RAW_ARTIFACT_FIELDS:
                redacted.append(path)
            else:
                redacted.extend(_collect_redacted_fields(nested, path))
    elif isinstance(value, list):
        for idx, nested in enumerate(value):
            redacted.extend(_collect_redacted_fields(nested, f"{prefix}[{idx}]"))
    return redacted


def _safe_artifact_index(job_detail: Any) -> Dict[str, Any]:
    payload = job_detail if isinstance(job_detail, dict) else {}
    result = payload.get("result") if isinstance(payload.get("result"), dict) else {}
    artifacts = []
    for key in ("artifacts", "artifact_refs", "artifactRefs"):
        candidate = result.get(key) or payload.get(key)
        if isinstance(candidate, list):
            artifacts = [item for item in candidate if isinstance(item, dict)]
            break

    summaries = []
    for key in ("summary", "compact_summary", "worker_summary"):
        value = result.get(key) or payload.get(key)
        if isinstance(value, str) and value:
            summaries.append({"field": key, "text": value})

    verification = result.get("verification") or result.get("verification_result") or payload.get("verification")
    replay = result.get("replay") or result.get("replay_instructions") or payload.get("replay")

    return {
        "artifacts": artifacts,
        "summaries": summaries,
        "verification": verification if isinstance(verification, (dict, list, str)) else None,
        "replay": replay if isinstance(replay, (dict, list, str)) else None,
        "redacted_fields": sorted(set(_collect_redacted_fields(payload))),
    }


@app.post("/api/user-input")
async def api_user_input(req: UserInputRequest):
    """Proxy user task from portal textbox to PT's /user-input queue."""
    async with httpx.AsyncClient(timeout=5.0) as client:
        try:
            r = await client.post(
                f"{PT_URL}/user-input",
                json={"message": req.message, "source": "portal"},
            )
            r.raise_for_status()
            return r.json()
        except Exception as exc:
            return {"status": "error", "message": str(exc)}


@app.get("/api/app/state")
async def api_app_state():
    """Aggregate portal status and PT runtime sections for the operator app."""
    portal_status = await api_status()

    async with httpx.AsyncClient(timeout=PROBE_TIMEOUT) as client:
        runtime, models, activity, jobs = await asyncio.gather(
            _fetch_pt_section(client, "/runtime", source="pt:/runtime", default={}),
            _fetch_pt_section(client, "/models", source="pt:/models", default={}),
            _fetch_pt_section(client, "/activity?limit=25", source="pt:/activity", default={"events": []}),
            _fetch_pt_section(client, "/v1/jobs", source="pt:/v1/jobs", default={"jobs": []}),
        )

    if not jobs.available:
        fallback_jobs = _normalize_jobs_payload(portal_status.get("supervisor_jobs", []))
        jobs = AppStateSection(
            available=bool(fallback_jobs),
            data={"jobs": fallback_jobs},
            error=jobs.error,
            source="portal:supervisor_jobs_fallback",
        )

    return {
        "portal": {
            "available": True,
            "source": "portal:/api/status",
            "data": portal_status,
        },
        "runtime": _dump_model(runtime),
        "models": _dump_model(models),
        "activity": _dump_model(activity),
        "jobs": _dump_model(jobs),
    }


@app.post("/api/swarm/preview")
async def api_swarm_preview(req: SwarmPreviewRequest):
    """Create a stateless five-role swarm preview; this route never dispatches."""
    return await _build_swarm_preview(req)


@app.post("/api/swarm/launch")
async def api_swarm_launch(req: SwarmLaunchRequest):
    """Launch approved preview assignments as PT-owned jobs; orama stores no job state."""
    if not req.approved:
        raise HTTPException(status_code=422, detail="approved=true is required")

    preview = await _build_swarm_preview(req)
    hardware_policy = preview.get("hardware_policy", {})
    if not hardware_policy.get("ok", False):
        raise HTTPException(
            status_code=409,
            detail={
                "blocked": True,
                "reason": "hardware_policy",
                "violations": hardware_policy.get("violations", []),
                "accepted_jobs": [],
            },
        )

    session_id = f"swarm-{uuid.uuid4().hex}"
    accepted_jobs: List[Dict[str, Any]] = []
    failed_jobs: List[Dict[str, Any]] = []
    async with httpx.AsyncClient(timeout=10.0) as client:
        for assignment in preview["assignments"]:
            metadata = {
                "role": assignment["role"],
                "specialization": assignment["specialization"],
                "session_id": session_id,
                "parent_orchestrator_id": "orama-portal",
                "artifact_policy": "summary_and_refs_only",
                "expected_output_shape": assignment["expected_output_shape"],
                "verification_rubric": assignment["verification_rubric"],
                "routing_source": assignment["routing_source"],
            }
            payload = {
                "intent": assignment["intent"],
                "prompt": preview["objective"],
                "backend_hint": assignment["backend_hint"],
                "constraints": {
                    "task_type": preview["task_type"],
                    "optimize_for": preview["optimize_for"],
                    "preferred_device": preview["preferred_device"],
                },
                "metadata": metadata,
            }
            try:
                r = await client.post(f"{PT_URL}/v1/jobs", json=payload)
                r.raise_for_status()
                data = r.json()
                accepted_jobs.append({
                    "role": assignment["role"],
                    "job_id": _extract_pt_job_id(data),
                    "response": data,
                })
            except Exception as exc:
                failed_jobs.append({
                    "role": assignment["role"],
                    "error": str(exc),
                    "request": payload,
                })

    return {
        "accepted": not failed_jobs,
        "blocked": False,
        "session_id": session_id,
        "accepted_jobs": accepted_jobs,
        "failed_jobs": failed_jobs,
        "preview": preview,
    }


@app.get("/api/jobs")
async def api_jobs_proxy(status: Optional[str] = None):
    params = {"status": status} if status else {}
    async with httpx.AsyncClient(timeout=5.0) as client:
        try:
            r = await client.get(f"{PT_URL}/v1/jobs", params=params)
            r.raise_for_status()
            return {"available": True, "source": "pt:/v1/jobs", "jobs": _normalize_jobs_payload(r.json())}
        except Exception as exc:
            return {"available": False, "source": "pt:/v1/jobs", "jobs": [], "error": str(exc)}


@app.get("/api/jobs/{job_id}")
async def api_job_detail_proxy(job_id: str):
    async with httpx.AsyncClient(timeout=5.0) as client:
        try:
            r = await client.get(f"{PT_URL}/v1/jobs/{job_id}")
            r.raise_for_status()
            return {"available": True, "source": "pt:/v1/jobs/{job_id}", "job": r.json()}
        except Exception as exc:
            return {"available": False, "source": "pt:/v1/jobs/{job_id}", "job": None, "error": str(exc)}


@app.post("/api/jobs/{job_id}/cancel")
async def api_job_cancel_proxy(job_id: str):
    async with httpx.AsyncClient(timeout=5.0) as client:
        try:
            r = await client.post(f"{PT_URL}/cancel", json={"job_id": job_id})
            r.raise_for_status()
            return {"available": True, "source": "pt:/cancel", "result": r.json()}
        except Exception as exc:
            return {"available": False, "source": "pt:/cancel", "result": None, "error": str(exc)}


@app.post("/api/jobs/{job_id}/replay")
async def api_job_replay_proxy(job_id: str):
    async with httpx.AsyncClient(timeout=5.0) as client:
        try:
            r = await client.post(f"{PT_URL}/replay", json={"job_id": job_id})
            r.raise_for_status()
            return {"available": True, "source": "pt:/replay", "result": r.json()}
        except Exception as exc:
            return {"available": False, "source": "pt:/replay", "result": None, "error": str(exc)}


@app.get("/api/jobs/{job_id}/artifacts")
async def api_job_artifacts_proxy(job_id: str):
    async with httpx.AsyncClient(timeout=5.0) as client:
        try:
            r = await client.get(f"{PT_URL}/v1/jobs/{job_id}")
            r.raise_for_status()
            return {
                "available": True,
                "source": "pt:/v1/jobs/{job_id}",
                "job_id": job_id,
                **_safe_artifact_index(r.json()),
            }
        except Exception as exc:
            return {
                "available": False,
                "source": "pt:/v1/jobs/{job_id}",
                "job_id": job_id,
                "artifacts": [],
                "summaries": [],
                "verification": None,
                "replay": None,
                "redacted_fields": [],
                "error": str(exc),
            }


def _parse_env_file(path: "Path") -> Dict[str, str]:
    """Parse a .env file into a dict. Handles KEY=VAL, KEY = VAL, inline comments."""
    result: Dict[str, str] = {}
    if not path.exists():
        return result
    try:
        for raw_line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            key = key.strip()
            val = val.strip()
            # Strip inline comments (but not comments inside quotes)
            if val and val[0] not in ('"', "'"):
                val = val.split("#")[0].strip()
            # Strip surrounding quotes
            if len(val) >= 2 and val[0] == val[-1] and val[0] in ('"', "'"):
                val = val[1:-1]
            if key:
                result[key] = val
    except Exception:
        pass
    return result


def _probe_tools_sync() -> Dict[str, Any]:
    """Probe all tools/APIs synchronously (called from thread pool). Returns availability dict."""
    import shutil, subprocess, socket as _sock

    tools: Dict[str, Any] = {}

    # ── Parse all env files ONCE into a merged dict ────────────────────────────
    _env_search_paths = [
        REPO_ROOT / ".env",
        REPO_ROOT / ".env.local",          # .local overrides base
        PERPETUA_TOOLS_ROOT / ".env",
        PERPETUA_TOOLS_ROOT / ".env.local",
    ]
    _env_cache: Dict[str, str] = {}
    for fpath in _env_search_paths:
        _env_cache.update(_parse_env_file(fpath))  # later paths override earlier

    def _key_state(env_var: str) -> tuple[bool, bool]:
        """Return (key_present, key_valid) — reads from process env or cached file parse."""
        val = os.getenv(env_var) or _env_cache.get(env_var, "")
        present = bool(val)
        valid = bool(
            val
            and not val.lower().startswith("your_")
            and not val.lower().startswith("sk-your")
            and val != "lm-studio"
            and len(val) > 8
        )
        return present, valid

    # ── Table-driven key probing ───────────────────────────────────────────────
    for env_var, label, group, _ in _ALL_KNOWN_KEYS:
        present, valid = _key_state(env_var)
        slug = env_var.lower().replace("_", "-")
        tools[slug] = {
            "ok": valid,
            "key_present": present,
            "label": label,
            "group": group,
            "env_var": env_var,
            "detail": f"{env_var} configured" if valid else (
                f"{env_var} set but invalid/placeholder" if present else f"{env_var} not configured"
            ),
        }

    # ── Codex CLI ──────────────────────────────────────────────────────────────
    codex_bin = shutil.which("codex") or "/opt/homebrew/bin/codex"
    codex_ok, codex_ver = False, ""
    if os.path.exists(codex_bin):
        try:
            r = subprocess.run([codex_bin, "--version"], capture_output=True, timeout=4)
            codex_ok = r.returncode == 0
            codex_ver = (r.stdout + r.stderr).decode("utf-8", errors="replace").strip().split("\n")[0]
        except Exception:
            pass
    tools["codex-cli"] = {"ok": codex_ok, "group": "cli", "detail": codex_ver if codex_ok else "not found — run scripts/setup_codex.sh"}

    # ── Gemini CLI ─────────────────────────────────────────────────────────────
    gemini_bin = shutil.which("gemini") or shutil.which("gemini-cli")
    gemini_ok, gemini_ver = False, ""
    if gemini_bin:
        try:
            r = subprocess.run([gemini_bin, "--version"], capture_output=True, timeout=4)
            raw = (r.stdout + r.stderr).decode("utf-8", errors="replace").strip()
            first_line = raw.split("\n")[0]
            has_error = any(x in raw for x in ("SyntaxError", "UnhandledPromise", "Error:", "TypeError"))
            gemini_ok = r.returncode == 0 and not has_error
            gemini_ver = first_line if gemini_ok else f"found but broken — {first_line[:60]}"
        except Exception:
            pass
    tools["gemini-cli"] = {"ok": gemini_ok, "group": "cli", "detail": gemini_ver if gemini_ver else "not found — npm i -g @google/gemini-cli"}

    # ── AlphaClaw Gateway ──────────────────────────────────────────────────────
    ac_port = int(os.getenv("ALPHACLAW_PORT", "18789"))
    ac_ok = False
    try:
        with _sock.create_connection(("127.0.0.1", ac_port), timeout=1.5):
            ac_ok = True
    except Exception:
        pass
    tools["alphaclaw-gateway"] = {
        "ok": ac_ok,
        "group": "gateway",
        "detail": f"127.0.0.1:{ac_port}" + (" ONLINE" if ac_ok else " OFFLINE — start AlphaClaw: ./start.sh"),
    }

    return tools


def _probe_cli_available(bin_name: str) -> bool:
    """Quick synchronous check: is a CLI binary present and functional?"""
    import shutil, subprocess
    p = shutil.which(bin_name)
    if not p:
        # Also try well-known paths
        known = {
            "codex": "/opt/homebrew/bin/codex",
            "gemini": "/opt/homebrew/bin/gemini",
        }
        p = known.get(bin_name, "")
    if not p or not os.path.exists(p):
        return False
    try:
        r = subprocess.run([p, "--version"], capture_output=True, timeout=4)
        return r.returncode == 0
    except Exception:
        return False


@app.get("/api/status")
async def api_status():
    # ── Dynamic IP resolution — always re-read from openclaw.json on every call ──
    # LAN is treated as always-changing: the Win machine can get a new DHCP lease,
    # reboot, or move subnets at any time.  We re-resolve on every status poll
    # (every 10s) so the portal stays accurate without a restart.
    try:
        _dyn_win_lms  = [_get_win_lms_url()]      # re-reads openclaw.json each time
        _dyn_ollama_win = _get_win_ollama_url()
    except Exception:
        _dyn_win_lms  = LMS_WIN_ENDPOINTS
        _dyn_ollama_win = OLLAMA_WIN

    async with httpx.AsyncClient() as client:
        (
            (pt_ok, pt_ver),
            (us_ok, us_ver),
            (lm_mac_ok, lm_mac_models),
            ol_win_result,
            ol_mac_result,
            activity_events,
            agents,
            routing,
            queue_depth,
            supervisor_jobs,
            *lm_win_results,
        ) = await asyncio.gather(
            _probe_http(client, f"{PT_URL}/health"),
            _probe_http(client, f"{US_URL}/health"),
            _probe_lms_models(client, LMS_MAC_ENDPOINT, LMS_API_TOKEN),
            _probe_ollama_models(client, _dyn_ollama_win),
            _probe_ollama_models(client, OLLAMA_MAC),
            _probe_activity(client),
            _probe_agents(client),
            _probe_routing(client),
            _probe_queue_depth(client),
            _probe_supervisor_jobs(client),
            *[_probe_lms_models(client, ep, LMS_API_TOKEN) for ep in _dyn_win_lms],
        )

    # ── Gossip: if Win LMS responded at a new IP, write it back to openclaw.json ─
    # This makes discovery self-healing: once the portal hits the Win machine it
    # gossips the live IP back so every other process picks it up on the next read.
    if lm_win_results:
        _win_ok, _ = lm_win_results[0]
        if _win_ok and _dyn_win_lms:
            _probed_ip = _dyn_win_lms[0].split("://")[-1].split(":")[0]
            try:
                from utils.ip_resolver import write_win_ip_to_openclaw_json
                write_win_ip_to_openclaw_json(_probed_ip)
            except Exception as _gossip_exc:
                log.warning("ip gossip write failed: %s", _gossip_exc)

    async with httpx.AsyncClient() as _ps_client:
        ol_mac_busy = await _probe_ollama_ps(_ps_client, OLLAMA_MAC)

    services: Dict[str, Any] = {
        "perplexity_tools": {"ok": pt_ok, "version": pt_ver, "url": PT_URL},
        "ultrathink": {"ok": us_ok, "version": us_ver, "url": US_URL},
        "lmstudio_mac": {"ok": lm_mac_ok, "models": lm_mac_models, "url": LMS_MAC_ENDPOINT},
        "ollama_win": {"ok": ol_win_result[0], "models": ol_win_result[1], "url": _dyn_ollama_win},
        "ollama_mac": {"ok": ol_mac_result[0], "models": ol_mac_result[1], "url": OLLAMA_MAC, "busy": ol_mac_busy},
    }

    if len(_dyn_win_lms) == 1:
        ok, models = lm_win_results[0]
        services["lmstudio_win"] = {"ok": ok, "models": models, "url": _dyn_win_lms[0]}
    else:
        for i, (ok, models) in enumerate(lm_win_results):
            services[f"lmstudio_win_{i}"] = {"ok": ok, "models": models, "url": _dyn_win_lms[i]}

    hardware_policy = _hardware_policy_status(services)

    # Tools + CLI availability (sync checks in thread pool — no extra HTTP calls)
    loop = asyncio.get_event_loop()
    tools = await loop.run_in_executor(None, _probe_tools_sync)

    return {
        "portal_version": VERSION,
        "services": services,
        "activity": activity_events,
        "agents": agents,
        "routing": routing,
        "hardware_policy": hardware_policy,
        "openrouter": {
            "policy_active": True,
            "api_key_present": bool(os.getenv("OPENROUTER_API_KEY")),
            "default_fallback_chain": OPENROUTER_FREE_FALLBACKS,
            "gemini_policy": "analyzer-only",
        },
        "queue_depth": queue_depth,
        "supervisor_jobs": supervisor_jobs,
        "tools": tools,
        "codex_available": tools.get("codex-cli", {}).get("ok", False),
        "gemini_available": tools.get("gemini-cli", {}).get("ok", False),
    }


@app.get("/api/hardware-policy")
async def api_hardware_policy():
    status = await api_status()
    return status.get("hardware_policy", {})


@app.get("/api/tools")
async def api_tools():
    """Return availability of all configured tools and APIs."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _probe_tools_sync)


class ConfigureToolRequest(BaseModel):
    tool: str        # e.g. "brave", "perplexity", "claude_api"
    env_var: str     # e.g. "BRAVE_API_KEY"
    value: str       # the API key value


# Simple in-memory rate limiter: max 5 configure-tool calls per 60s (per portal process)
_CONFIGURE_RATE: Dict[str, list] = {}  # key → list of epoch timestamps
_CONFIGURE_MAX_CALLS = 5
_CONFIGURE_WINDOW_SEC = 60


def _check_rate_limit(key: str) -> bool:
    """Return True if request is allowed, False if rate limit exceeded."""
    now = time.time()
    window_start = now - _CONFIGURE_WINDOW_SEC
    calls = [t for t in _CONFIGURE_RATE.get(key, []) if t > window_start]
    if len(calls) >= _CONFIGURE_MAX_CALLS:
        return False
    calls.append(now)
    _CONFIGURE_RATE[key] = calls
    return True


# ── All known API keys (mirrors AlphaClaw kKnownVars + PT-specific) ───────────
# Each entry: (env_var, label, group, hint_link)
_ALL_KNOWN_KEYS = [
    # AI providers
    ("ANTHROPIC_API_KEY",  "Claude (Anthropic)",   "ai",       "https://console.anthropic.com/"),
    ("OPENAI_API_KEY",     "OpenAI",               "ai",       "https://platform.openai.com/api-keys"),
    ("GEMINI_API_KEY",     "Gemini (Google)",      "ai",       "https://aistudio.google.com/app/apikey"),
    ("MISTRAL_API_KEY",    "Mistral",              "ai",       "https://console.mistral.ai/"),
    ("GROQ_API_KEY",       "Groq",                 "ai",       "https://console.groq.com/keys"),
    ("VOYAGE_API_KEY",     "Voyage AI",            "ai",       "https://dash.voyageai.com/"),
    # Tools & search
    ("BRAVE_API_KEY",      "Brave Search",         "tools",    "https://brave.com/search/api/"),
    ("PERPLEXITY_API_KEY", "Perplexity",           "tools",    "https://www.perplexity.ai/settings/api"),
    ("DEEPGRAM_API_KEY",   "Deepgram (speech)",    "tools",    "https://console.deepgram.com/"),
    ("ELEVENLABS_API_KEY", "ElevenLabs (TTS)",     "tools",    "https://elevenlabs.io/"),
    # Channels
    ("TELEGRAM_BOT_TOKEN", "Telegram Bot",         "channels", "https://t.me/BotFather"),
    ("DISCORD_BOT_TOKEN",  "Discord Bot",          "channels", "https://discord.com/developers/applications"),
    ("SLACK_BOT_TOKEN",    "Slack Bot",            "channels", "https://api.slack.com/apps"),
    ("SLACK_APP_TOKEN",    "Slack App (xapp-...)", "channels", "https://api.slack.com/apps"),
    # GitHub
    ("GITHUB_TOKEN",       "GitHub Token",         "github",   "https://github.com/settings/tokens"),
]

# Env vars that are safe to write via the portal
_ALLOWED_ENV_VARS = {entry[0] for entry in _ALL_KNOWN_KEYS}

# Env files to write to (in priority order — first writable one wins)
_ENV_WRITE_TARGETS = [
    REPO_ROOT / ".env.local",   # most specific — write here first
    REPO_ROOT / ".env",
    PERPETUA_TOOLS_ROOT / ".env.local",
    PERPETUA_TOOLS_ROOT / ".env",
]


def _write_env_var(env_var: str, value: str) -> tuple[bool, str]:
    """Write/update an env var in .env.local. Atomic write + file lock to prevent races."""
    import fcntl, tempfile, re as _re
    if env_var not in _ALLOWED_ENV_VARS:
        return False, f"Env var {env_var!r} not in allowlist"
    if not value or len(value) < 4:
        return False, "Value too short"
    # Sanitize: strip newlines + shell-injection chars (backticks, single quotes, semicolons)
    safe_value = _re.sub(r'[`\'\n\r;$\\]', "", value).replace('"', "")
    if len(safe_value) < 4:
        return False, "Value too short after sanitization"

    target = REPO_ROOT / ".env.local"
    lock_file = target.with_suffix(".lock")

    try:
        # File lock: prevents concurrent writes
        with open(lock_file, "w") as lf:
            fcntl.flock(lf, fcntl.LOCK_EX | fcntl.LOCK_NB)
            try:
                # Parse existing .env.local
                lines = _parse_env_file(target)
                # Update or insert
                lines[env_var] = safe_value
                # Reconstruct file content preserving other vars
                raw_lines = target.read_text().splitlines() if target.exists() else []
                updated = False
                for i, raw in enumerate(raw_lines):
                    stripped = raw.strip()
                    if stripped.startswith(f"{env_var}=") or stripped.startswith(f"# {env_var}="):
                        raw_lines[i] = f'{env_var}="{safe_value}"'
                        updated = True
                        break
                if not updated:
                    raw_lines.append(f'{env_var}="{safe_value}"')
                new_content = "\n".join(raw_lines) + "\n"
                # Atomic write: tmp file in same dir + rename
                with tempfile.NamedTemporaryFile(
                    mode="w", dir=target.parent, prefix=".env.tmp.", delete=False
                ) as tf:
                    tf.write(new_content)
                    tf_path = Path(tf.name)
                tf_path.replace(target)
                return True, f"Saved to {target.name}"
            finally:
                fcntl.flock(lf, fcntl.LOCK_UN)
    except BlockingIOError:
        return False, "Config file is locked by another request — retry in a moment"
    except Exception as exc:
        return False, f"Write failed: {exc}"


@app.post("/api/configure-tool")
async def api_configure_tool(req: ConfigureToolRequest):
    """Write an API key to .env.local — allows portal-based configuration with no terminal.
    Rate-limited to 5 calls/60s to prevent credential brute-forcing.
    """
    from fastapi import HTTPException
    rl_key = f"configure:{req.env_var}"
    if not _check_rate_limit(rl_key):
        raise HTTPException(status_code=429, detail="Rate limit exceeded — max 5 changes/min")
    loop = asyncio.get_event_loop()
    ok, msg = await loop.run_in_executor(None, _write_env_var, req.env_var, req.value)
    if ok:
        # Reload env in current process so probes pick it up immediately
        import re as _re
        safe = _re.sub(r'[`\'\n\r;$\\]', "", req.value).replace('"', "")
        os.environ[req.env_var] = safe
    return {"ok": ok, "message": msg}


# ── Supervisor jobs proxy ─────────────────────────────────────────────────────

@app.get("/api/v1/jobs")
async def api_get_jobs(status: Optional[str] = None):
    """Proxy to PT's /v1/jobs — used by the supervisor jobs panel JS poller."""
    params = {"status": status} if status else {}
    async with httpx.AsyncClient(timeout=5.0) as client:
        try:
            r = await client.get(f"{PT_URL}/v1/jobs", params=params)
            r.raise_for_status()
            return r.json()
        except Exception as exc:
            return []


# ── Service lifecycle controls ────────────────────────────────────────────────

def _pid_on_port(port: int) -> Optional[int]:
    """Return PID listening on port, or None. Uses lsof on macOS/Linux."""
    import shutil
    # lsof is available on macOS and most Linux distros
    lsof = shutil.which("lsof")
    if lsof:
        try:
            out = subprocess.check_output(
                [lsof, "-ti", f"tcp:{port}"], stderr=subprocess.DEVNULL
            ).decode().strip()
            pid_str = out.split("\n")[0].strip()
            return int(pid_str) if pid_str.isdigit() else None
        except Exception:
            pass
    # Fallback: ss (Linux)
    ss = shutil.which("ss")
    if ss:
        try:
            out = subprocess.check_output(
                ["ss", "-tlnp", f"sport = :{port}"], stderr=subprocess.DEVNULL
            ).decode()
            import re
            m = re.search(r'pid=(\d+)', out)
            return int(m.group(1)) if m else None
        except Exception:
            pass
    return None


_SERVICE_PORTS = {"pt": 8000, "orama": 8001, "portal": 8002}
_SERVICE_CMDS = {
    "pt":     ["python", "-m", "uvicorn", "orchestrator.fastapi_app:app", "--host", "0.0.0.0", "--port", "8000"],
    "orama":  ["python", "-m", "uvicorn", "api_server:app", "--host", "0.0.0.0", "--port", "8001"],
    "portal": ["python", "-m", "uvicorn", "portal_server:app", "--host", "0.0.0.0", "--port", "8002"],
}


@app.post("/api/stop")
async def api_stop():
    """Kill all three orama services (PT :8000, orama :8001, portal :8002)."""
    killed = []
    for name, port in _SERVICE_PORTS.items():
        pid = _pid_on_port(port)
        if pid:
            try:
                os.kill(pid, signal.SIGTERM)
                killed.append(f"{name}:{port} (PID {pid})")
            except Exception as exc:
                killed.append(f"{name}:{port} kill failed: {exc}")
        else:
            killed.append(f"{name}:{port} not running")
    return {"ok": True, "message": "Stop sent — " + "; ".join(killed)}


@app.post("/api/restart/{service}")
async def api_restart(service: str):
    """Kill and restart a named service (pt | orama | portal).
    The service is restarted as a detached background process with the same working
    directory and inherited environment variables.
    """
    if service not in _SERVICE_PORTS:
        return {"ok": False, "message": f"Unknown service '{service}' — use: pt, orama, portal"}
    port = _SERVICE_PORTS[service]

    # Kill current process
    pid = _pid_on_port(port)
    if pid:
        try:
            os.kill(pid, signal.SIGTERM)
            await asyncio.sleep(1.2)
        except Exception:
            pass

    # Determine working dir + python
    if service == "pt":
        cwd = str(PERPETUA_TOOLS_ROOT)
        py = sys.executable
        env = {**os.environ, "PYTHONPATH": cwd}
        cmd = [py, "-m", "uvicorn", "orchestrator.fastapi_app:app",
               "--host", "0.0.0.0", "--port", str(port)]
    else:
        cwd = str(REPO_ROOT)
        py = sys.executable
        env = {**os.environ, "PYTHONPATH": cwd}
        module = "api_server:app" if service == "orama" else "portal_server:app"
        cmd = [py, "-m", "uvicorn", module, "--host", "0.0.0.0", "--port", str(port)]

    log_path = REPO_ROOT / ".logs" / f"{service}.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(log_path, "ab") as lf:
            subprocess.Popen(
                cmd, cwd=cwd, env=env,
                stdout=lf, stderr=lf,
                start_new_session=True,
            )
        return {"ok": True, "message": f"Restarting {service} on :{port} — check {log_path.name}"}
    except Exception as exc:
        return {"ok": False, "message": f"Restart failed: {exc}"}


@app.post("/api/rediscover")
async def api_rediscover():
    """Re-run LAN discovery (discover.py --force) and return updated Win IP."""
    discover_script = Path.home() / ".openclaw" / "scripts" / "discover.py"
    if not discover_script.exists():
        return {"ok": False, "message": f"discover.py not found at {discover_script}"}
    loop = asyncio.get_event_loop()

    def _run():
        try:
            result = subprocess.run(
                [sys.executable, str(discover_script), "--force"],
                capture_output=True, text=True, timeout=35,
            )
            stdout = (result.stdout or "").strip()
            stderr = (result.stderr or "").strip()
            ok = result.returncode == 0
            summary = stdout.splitlines()[-1] if stdout else (stderr.splitlines()[-1] if stderr else "done")
            return {"ok": ok, "message": f"Discover {'OK' if ok else 'failed'}: {summary[:120]}"}
        except subprocess.TimeoutExpired:
            return {"ok": False, "message": "discover.py timed out (>35s)"}
        except Exception as exc:
            return {"ok": False, "message": f"discover.py error: {exc}"}

    return await loop.run_in_executor(None, _run)


class SpawnAgentRequest(BaseModel):
    agent: str
    task: str
    model: str = ""


@app.post("/api/spawn-agent")
async def api_spawn_agent(req: SpawnAgentRequest):
    """Dispatch a task to a named agent (codex, gemini, lmstudio-mac, lmstudio-win, all).
    Runs synchronously in a threadpool so FastAPI stays responsive.
    Windows GPU requests are serialized by the _WIN_GPU_LOCK in spawn_agents.py.
    """
    import importlib.util
    _scripts_dir = REPO_ROOT / "scripts"
    # Cache spawn_agents module so _WIN_GPU_LOCK is a singleton (not re-created per request)
    _mod = sys.modules.get("spawn_agents")
    if _mod is None:
        _spec = importlib.util.spec_from_file_location("spawn_agents", _scripts_dir / "spawn_agents.py")
        if _spec is None or _spec.loader is None:
            return {"ok": False, "output": "spawn_agents.py not found in scripts/", "elapsed": 0}
        _mod = importlib.util.module_from_spec(_spec)
        # Register in sys.modules BEFORE exec_module so dataclass annotations resolve correctly
        sys.modules["spawn_agents"] = _mod
        _spec.loader.exec_module(_mod)  # type: ignore[union-attr]
    # Affinity pre-flight (non-blocking — logs warning only)
    try:
        _pt_root = str(PERPETUA_TOOLS_ROOT)
        if _pt_root not in sys.path:
            sys.path.insert(0, _pt_root)
        from orchestrator.alphaclaw_manager import validate_routing_affinity as _vra
        _agent_model = req.model
        _agent_platform = "mac"
        if _agent_model:
            _vra(_agent_model, _agent_platform)
            log.info("[portal] affinity OK: %s → %s", _agent_model, _agent_platform)
    except ImportError:
        pass  # PT not on sys.path — skip silently
    except Exception as _aff_exc:
        log.warning("[portal] affinity warning for spawn: %s", _aff_exc)
        # Non-fatal: let dispatch proceed; agent_launcher will hard-gate

    result = await _mod.dispatch(req.agent, req.task, model=req.model or None)
    return result


@app.get("/dashboard", response_class=None)
async def dashboard():
    """Serve the routing-dashboard.html SPA."""
    from fastapi.responses import FileResponse, HTMLResponse
    dashboard_path = REPO_ROOT / "docs" / "dashboard" / "routing-dashboard.html"
    if dashboard_path.exists():
        return FileResponse(str(dashboard_path), media_type="text/html")
    return HTMLResponse(
        f"<h2>Dashboard not found</h2><p>Expected: {dashboard_path}</p>",
        status_code=404,
    )


@app.get("/api/status-html")
async def api_status_html():
    """Return pre-rendered HTML fragments for async JS polling (no page reload)."""
    import datetime
    status = await api_status()
    svc = status.get("services", {})

    cards = []
    pt = svc.get("perplexity_tools", {})
    cards.append(_render_card(
        "Perpetua-Tools", pt.get("ok", False), pt.get("url", ""),
        role="orchestrator / cloud router",
        extra=f'<div class="version">{pt.get("version","")}</div>',
    ))
    us = svc.get("ultrathink", {})
    cards.append(_render_card(
        "orama API", us.get("ok", False), us.get("url", ""),
        role="5-stage reasoning bridge",
        extra=f'<div class="version">{us.get("version","")}</div>',
    ))
    lm_mac = svc.get("lmstudio_mac", {})
    cards.append(_render_card(
        "LM Studio — Mac", lm_mac.get("ok", False), lm_mac.get("url", ""),
        role="orchestrator + validator + presenter",
        models=lm_mac.get("models", []),
    ))
    for key, entry in svc.items():
        if key.startswith("lmstudio_win"):
            label = "LM Studio — Win" if key == "lmstudio_win" else f"LM Studio — {key}"
            cards.append(_render_card(
                label, entry.get("ok", False), entry.get("url", ""),
                role="coder/checker/refiner/executor/verifier",
                models=entry.get("models", []),
            ))
    ol_win = svc.get("ollama_win", {})
    cards.append(_render_card(
        "Ollama — Win (fallback)", ol_win.get("ok", False), ol_win.get("url", ""),
        models=ol_win.get("models", []),
    ))
    ol_mac = svc.get("ollama_mac", {})
    cards.append(_render_card(
        "Ollama — Mac (manager)", ol_mac.get("ok", False), ol_mac.get("url", ""),
        role="manager: qwen3.5:9b-nvfp4",
        models=ol_mac.get("models", []),
    ))

    routing_state = _read_routing_json()
    return {
        "cards": "\n".join(cards),
        "routing_section": _render_routing_section(status.get("routing")),
        "activity_section": _render_activity_section(status.get("activity", [])),
        "timestamp": datetime.datetime.now().strftime("%H:%M:%S"),
        "manager_alert": routing_state.get("manager_affinity_alert"),
    }


@app.get("/", response_class=None)
async def index():
    from fastapi.responses import HTMLResponse
    status = await api_status()
    html = _render_html(status)
    return HTMLResponse(content=html)


if __name__ == "__main__":
    uvicorn.run(app, host=PORTAL_HOST, port=PORTAL_PORT)
