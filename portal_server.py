#!/usr/bin/env python3
"""portal_server.py — Slate-grey LAN portal on port 8002.

Shows live status of PT, ultrathink, LM Studio Win/Mac, and Ollama Win/Mac.
All probes run concurrently via asyncio.gather.

Routes:
  GET /           HTML dashboard (meta-refresh every 10s)
  GET /api/status JSON status of all services
  GET /health     {"status": "ok", "version": "1.0.0-rc"}
"""
from __future__ import annotations

import asyncio
import logging
import os
from typing import Any, Dict, List

import httpx
import uvicorn
from fastapi import FastAPI

log = logging.getLogger("ultrathink.portal")
logging.basicConfig(level=logging.INFO)

VERSION = "1.0.0-rc"

# ── Config ─────────────────────────────────────────────────────────────────────

PORTAL_HOST = os.getenv("PORTAL_HOST", "0.0.0.0")
PORTAL_PORT = int(os.getenv("PORTAL_PORT", "8002"))

PT_URL = os.getenv("ORCHESTRATOR_ENDPOINT", "http://localhost:8000")
US_URL = os.getenv("ULTRATHINK_ENDPOINT", "http://localhost:8001")

LMS_WIN_ENDPOINTS: List[str] = [
    ep.strip()
    for ep in os.getenv("LM_STUDIO_WIN_ENDPOINTS", "http://192.168.1.100:1234").split(",")
    if ep.strip()
]
LMS_MAC_ENDPOINT = os.getenv("LM_STUDIO_MAC_ENDPOINT", "http://localhost:1234")
LMS_API_TOKEN = os.getenv("LM_STUDIO_API_TOKEN", "")

OLLAMA_WIN = os.getenv("OLLAMA_WINDOWS_ENDPOINT", "http://192.168.1.100:11434")
OLLAMA_MAC = os.getenv("OLLAMA_MAC_ENDPOINT", "http://localhost:11434")

PROBE_TIMEOUT = 3.0

app = FastAPI(title="UltraThink LAN Portal", version=VERSION)

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
  .ev-who{{color:#38bdf8;font-size:.7rem;white-space:nowrap;min-width:8rem}}
  .ev-tag{{font-size:.65rem;border-radius:2px;padding:.05rem .3rem;white-space:nowrap}}
  .tag-reply{{background:#4ade8020;color:#4ade80}}
  .tag-query{{background:#38bdf820;color:#7dd3fc}}
  .tag-error{{background:#f8717120;color:#f87171}}
  .tag-other{{background:#64748b40;color:#94a3b8}}
  .ev-msg{{color:#cbd5e1;font-size:.75rem;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;flex:1}}
  .none{{color:#64748b;font-size:.75rem;padding:.75rem}}
</style>
</head>
<body>
<h1>UltraThink LAN Portal <span class="version">v{version}</span></h1>
<div class="grid">
{cards}
</div>
{activity_section}
<div class="footer">Auto-refresh every 10s &bull; {timestamp}</div>
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
        "Ollama — Mac (fallback)", ol_mac.get("ok", False), ol_mac.get("url", ""),
        models=ol_mac.get("models", []),
    ))

    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    activity_events = status.get("activity", [])
    return HTML_TEMPLATE.format(
        version=VERSION,
        cards="\n".join(cards),
        activity_section=_render_activity_section(activity_events),
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


# ── Routes ─────────────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {"status": "ok", "version": VERSION}


async def _probe_activity(client: httpx.AsyncClient) -> List[Dict[str, Any]]:
    try:
        r = await client.get(f"{PT_URL}/activity?limit=15", timeout=PROBE_TIMEOUT)
        r.raise_for_status()
        return r.json().get("events", [])
    except Exception:
        return []


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
            *lm_win_results,
        ) = await asyncio.gather(
            _probe_http(client, f"{PT_URL}/health"),
            _probe_http(client, f"{US_URL}/health"),
            _probe_lms_models(client, LMS_MAC_ENDPOINT, LMS_API_TOKEN),
            _probe_ollama_models(client, OLLAMA_WIN),
            _probe_ollama_models(client, OLLAMA_MAC),
            _probe_activity(client),
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

    return {"portal_version": VERSION, "services": services, "activity": activity_events}


@app.get("/", response_class=None)
async def index():
    from fastapi.responses import HTMLResponse
    status = await api_status()
    html = _render_html(status)
    return HTMLResponse(content=html)


if __name__ == "__main__":
    uvicorn.run(app, host=PORTAL_HOST, port=PORTAL_PORT)
