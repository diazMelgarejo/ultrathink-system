#!/usr/bin/env python3
"""portal_server.py — Slate-grey LAN portal on port 8002.

Shows live status of PT, ultrathink, LM Studio Win/Mac, and Ollama Win/Mac.
All probes run concurrently via asyncio.gather.

Routes:
  GET  /           HTML dashboard (meta-refresh every 10s)
  GET  /api/status JSON status of all services
  POST /api/user-input  proxy to PT /user-input (portal textbox handler)
  GET  /health     {"status": "ok", "version": "0.9.9.7"}
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List

import httpx
import uvicorn
from fastapi import FastAPI
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

VERSION = "0.9.9.7"

# ── Config ─────────────────────────────────────────────────────────────────────

PORTAL_HOST = os.getenv("PORTAL_HOST", "0.0.0.0")
PORTAL_PORT = int(os.getenv("PORTAL_PORT", "8002"))

PT_URL = os.getenv("ORCHESTRATOR_ENDPOINT", "http://localhost:8000")
US_URL = os.getenv("ULTRATHINK_ENDPOINT", "http://localhost:8001")

LMS_WIN_ENDPOINTS: List[str] = [
    ep.strip()
    for ep in os.getenv("LM_STUDIO_WIN_ENDPOINTS", "http://192.168.254.108:1234").split(",")
    if ep.strip()
]
LMS_MAC_ENDPOINT = os.getenv("LM_STUDIO_MAC_ENDPOINT", "http://192.168.254.110:1234")
LMS_API_TOKEN = os.getenv("LM_STUDIO_API_TOKEN", "")

OLLAMA_WIN = os.getenv("OLLAMA_WINDOWS_ENDPOINT", "http://192.168.254.108:11434")
OLLAMA_MAC = os.getenv("OLLAMA_MAC_ENDPOINT", "http://127.0.0.1:11434")

PROBE_TIMEOUT = 3.0

REPO_ROOT = Path(__file__).resolve().parent
PERPETUA_TOOLS_ROOT = Path(
    os.getenv("PERPETUA_TOOLS_ROOT", REPO_ROOT.parent / "perplexity-api" / "Perpetua-Tools")
)

app = FastAPI(title="UltraThink LAN Portal", version=VERSION)
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
<meta http-equiv="refresh" content="10">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>UltraThink LAN Portal</title>
<style>
  *{{box-sizing:border-box;margin:0;padding:0}}
  body{{background:#475569;color:#f8fafc;font-family:monospace;font-size:14px;padding:1.5rem}}
  h1{{font-size:1.25rem;letter-spacing:.05em;margin-bottom:1rem;color:#38bdf8}}
  .grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:1rem}}
  .card{{background:#334155;border:1px solid #64748b;border-radius:4px;padding:1rem}}
  .card-title{{font-size:.75rem;letter-spacing:.1em;text-transform:uppercase;color:#94a3b8;margin-bottom:.5rem}}
  .badge{{display:inline-block;padding:.15rem .5rem;border-radius:2px;font-size:.75rem;margin-bottom:.5rem}}
  .ok{{color:#4ade80}}
  .err{{color:#f87171}}
  .warn{{color:#fbbf24}}
  .url{{color:#38bdf8;font-size:.75rem}}
  .role{{color:#94a3b8;font-size:.75rem}}
  .models{{margin-top:.5rem}}
  .model{{color:#cbd5e1;font-size:.75rem;padding:.1rem 0}}
  .footer{{margin-top:1.5rem;font-size:.7rem;color:#64748b}}
  .version{{color:#64748b;font-size:.7rem}}
  .section{{margin-top:1.5rem}}
  .section-title{{font-size:.8rem;letter-spacing:.1em;text-transform:uppercase;color:#38bdf8;margin-bottom:.75rem;border-bottom:1px solid #38bdf840;padding-bottom:.25rem}}
  .feed{{background:#334155;border:1px solid #64748b;border-radius:4px;overflow:hidden}}
  .ev{{display:flex;gap:.5rem;padding:.4rem .75rem;border-bottom:1px solid #3f536640;align-items:baseline}}
  .ev:last-child{{border-bottom:none}}
  .ev-ts{{color:#64748b;font-size:.65rem;white-space:nowrap;min-width:5rem}}
  .ev-who{{color:#38bdf8;font-size:.7rem;white-space:nowrap;min-width:9rem}}
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
</style>
</head>
<body>
<h1>UltraThink LAN Portal <span class="version">v{version}</span></h1>
<div class="grid">
{cards}
</div>
{routing_section}
{hardware_policy_section}
{agent_dispatch_section}
{agent_state_section}
{activity_section}
{input_section}
<div class="footer">Auto-refresh every 10s &bull; {timestamp}</div>
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


def _render_agent_dispatch_section(agent_availability: Dict[str, bool]) -> str:
    """Render the Agent Dispatch panel with live availability badges."""
    AGENTS = [
        ("codex",         "Codex",              "CLI · local"),
        ("gemini",        "Gemini CLI",          "CLI · local"),
        ("lmstudio-mac",  "LM Studio Mac",       "HTTP · .110"),
        ("lmstudio-win",  "LM Studio Win",       "HTTP · .101 GPU"),
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


def _render_html(status: Dict[str, Any]) -> str:
    import datetime

    cards = []
    svc = status.get("services", {})

    # PT
    pt = svc.get("perplexity_tools", {})
    cards.append(_render_card(
        "Perplexity-Tools", pt.get("ok", False), pt.get("url", ""),
        role="orchestrator / cloud router",
        extra=f'<div class="version">{pt.get("version","")}</div>',
    ))

    # US
    us = svc.get("ultrathink", {})
    cards.append(_render_card(
        "UltraThink API", us.get("ok", False), us.get("url", ""),
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
        role="manager: qwen3.5-local",
        models=ol_mac.get("models", []),
    ))

    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    activity_events = status.get("activity", [])
    routing = status.get("routing")
    agents = status.get("agents", [])
    queue_depth = status.get("queue_depth", 0)
    hardware_policy = status.get("hardware_policy")
    # Agent dispatch availability — derived from service probes already in status
    svc = status.get("services", {})
    agent_availability = {
        "lmstudio-mac": svc.get("lmstudio_mac", {}).get("ok", False),
        "lmstudio-win": (
            svc.get("lmstudio_win", {}).get("ok", False)
            or any(v.get("ok") for k, v in svc.items() if k.startswith("lmstudio_win_"))
        ),
        "codex": status.get("codex_available", False),
        "gemini": status.get("gemini_available", False),
    }
    return HTML_TEMPLATE.format(
        version=VERSION,
        cards="\n".join(cards),
        routing_section=_render_routing_section(routing),
        hardware_policy_section=_render_hardware_policy_section(hardware_policy),
        agent_dispatch_section=_render_agent_dispatch_section(agent_availability),
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
            *lm_win_results,
        ) = await asyncio.gather(
            _probe_http(client, f"{PT_URL}/health"),
            _probe_http(client, f"{US_URL}/health"),
            _probe_lms_models(client, LMS_MAC_ENDPOINT, LMS_API_TOKEN),
            _probe_ollama_models(client, OLLAMA_WIN),
            _probe_ollama_models(client, OLLAMA_MAC),
            _probe_activity(client),
            _probe_agents(client),
            _probe_routing(client),
            _probe_queue_depth(client),
            *[_probe_lms_models(client, ep, LMS_API_TOKEN) for ep in LMS_WIN_ENDPOINTS],
        )

    services: Dict[str, Any] = {
        "perplexity_tools": {"ok": pt_ok, "version": pt_ver, "url": PT_URL},
        "ultrathink": {"ok": us_ok, "version": us_ver, "url": US_URL},
        "lmstudio_mac": {"ok": lm_mac_ok, "models": lm_mac_models, "url": LMS_MAC_ENDPOINT},
        "ollama_win": {"ok": ol_win_result[0], "models": ol_win_result[1], "url": OLLAMA_WIN},
        "ollama_mac": {"ok": ol_mac_result[0], "models": ol_mac_result[1], "url": OLLAMA_MAC},
    }

    if len(LMS_WIN_ENDPOINTS) == 1:
        ok, models = lm_win_results[0]
        services["lmstudio_win"] = {"ok": ok, "models": models, "url": LMS_WIN_ENDPOINTS[0]}
    else:
        for i, (ok, models) in enumerate(lm_win_results):
            services[f"lmstudio_win_{i}"] = {"ok": ok, "models": models, "url": LMS_WIN_ENDPOINTS[i]}

    hardware_policy = _hardware_policy_status(services)

    # CLI agent availability (cheap sync checks, run in default thread pool)
    loop = asyncio.get_event_loop()
    codex_avail, gemini_avail = await asyncio.gather(
        loop.run_in_executor(None, _probe_cli_available, "codex"),
        loop.run_in_executor(None, _probe_cli_available, "gemini"),
    )

    return {
        "portal_version": VERSION,
        "services": services,
        "activity": activity_events,
        "agents": agents,
        "routing": routing,
        "hardware_policy": hardware_policy,
        "queue_depth": queue_depth,
        "codex_available": codex_avail,
        "gemini_available": gemini_avail,
    }


@app.get("/api/hardware-policy")
async def api_hardware_policy():
    status = await api_status()
    return status.get("hardware_policy", {})


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
    import importlib.util, sys as _sys
    _scripts_dir = REPO_ROOT / "scripts"
    _spec = importlib.util.spec_from_file_location("spawn_agents", _scripts_dir / "spawn_agents.py")
    if _spec is None or _spec.loader is None:
        return {"ok": False, "output": "spawn_agents.py not found in scripts/", "elapsed": 0}
    _mod = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(_mod)  # type: ignore[union-attr]
    result = await _mod.dispatch(req.agent, req.task, model=req.model or None)
    return result


@app.get("/", response_class=None)
async def index():
    from fastapi.responses import HTMLResponse
    status = await api_status()
    html = _render_html(status)
    return HTMLResponse(content=html)


if __name__ == "__main__":
    uvicorn.run(app, host=PORTAL_HOST, port=PORTAL_PORT)
