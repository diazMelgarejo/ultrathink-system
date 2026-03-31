"""
Portal server — minimal LAN health dashboard for ultrathink v1.0 RC.
Port 8002, slate-grey theme, inline CSS, meta refresh 10s.
Shows status of all services: Perplexity Tools, Ultrathink, LM Studio (Mac/Win), Ollama.
"""
import os
import asyncio
from datetime import datetime
from fastapi import FastAPI, Response
from fastapi.responses import HTMLResponse
import httpx

try:
    from network_autoconfig import NetworkAutoConfig as _NetCfg
    _net = _NetCfg()
except Exception:
    _net = None

app = FastAPI(title="ultrathink-portal", version="1.0.0-rc")

# === ENV CONFIG ===
PORTAL_PORT = int(os.getenv("PORTAL_PORT", "8002"))
PORTAL_HOST = os.getenv("PORTAL_HOST", "0.0.0.0")

LMS_MAC_ENDPOINT = os.getenv("LM_STUDIO_MAC_ENDPOINT", "http://localhost:1234")
LMS_WIN_ENDPOINTS = [
    s.strip()
    for s in os.getenv(
        "LM_STUDIO_WIN_ENDPOINTS", "http://192.168.1.100:1234"
    ).split(",")
]
LMS_API_TOKEN = os.getenv("LM_STUDIO_API_TOKEN", "")

PERPLEXITY_ENDPOINT = os.getenv("PERPLEXITY_ENDPOINT", "http://localhost:8000")
ULTRATHINK_ENDPOINT = os.getenv("ULTRATHINK_ENDPOINT", "http://localhost:8001")

OLLAMA_MAC_ENDPOINT = os.getenv(
    "OLLAMA_MAC_ENDPOINT", "http://192.168.1.101:11434"
)
OLLAMA_WIN_ENDPOINT = os.getenv(
    "OLLAMA_WINDOWS_ENDPOINT", "http://192.168.1.100:11434"
)


async def check_health(endpoint: str, timeout: float = 2.0) -> dict:
    """Check health of a service endpoint. Returns {ok, version, models, error}."""
    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            # Try /health first
            try:
                resp = await client.get(f"{endpoint}/health")
                if resp.status_code == 200:
                    data = resp.json()
                    return {
                        "ok": True,
                        "status": "ok",
                        "version": data.get("version", ""),
                    }
            except:
                pass

            # Try /v1/models (LM Studio, Ollama)
            try:
                resp = await client.get(f"{endpoint}/v1/models")
                if resp.status_code == 200:
                    data = resp.json()
                    models = [m.get("id") for m in data.get("data", [])]
                    return {
                        "ok": True,
                        "status": "ok",
                        "models": models,
                    }
            except:
                pass

            return {"ok": False, "error": "No health endpoint found"}
        except (httpx.RequestError, httpx.HTTPStatusError, Exception) as e:
            return {"ok": False, "error": str(e)}


@app.get("/health", response_class=Response)
async def health():
    """Simple health check for orchestration."""
    return Response("OK", status_code=200)


@app.get("/api/status")
async def api_status():
    """JSON API endpoint — status of all services."""
    # Check all services concurrently
    perplexity_status = await check_health(PERPLEXITY_ENDPOINT)
    ultrathink_status = await check_health(ULTRATHINK_ENDPOINT)
    lms_mac_status = await check_health(LMS_MAC_ENDPOINT)

    lms_win_statuses = []
    for endpoint in LMS_WIN_ENDPOINTS:
        status = await check_health(endpoint)
        lms_win_statuses.append({"endpoint": endpoint, **status})

    ollama_mac_status = await check_health(OLLAMA_MAC_ENDPOINT)
    ollama_win_status = await check_health(OLLAMA_WIN_ENDPOINT)

    return {
        "timestamp": datetime.utcnow().isoformat(),
        "portal_version": "1.0.0-rc",
        "orchestrator": "mac-studio",
        "services": {
            "perplexity_tools": perplexity_status,
            "ultrathink": ultrathink_status,
            "lmstudio_mac": {
                "endpoint": LMS_MAC_ENDPOINT,
                "role": "orchestrator+validator",
                "context": 4096,
                **lms_mac_status,
            },
            "lmstudio_win": lms_win_statuses,
            "ollama_mac": {
                "endpoint": OLLAMA_MAC_ENDPOINT,
                **ollama_mac_status,
            },
            "ollama_win": {
                "endpoint": OLLAMA_WIN_ENDPOINT,
                **ollama_win_status,
            },
        },
    }


@app.get("/api/lan-agents")
async def lan_agents():
    """
    Discover running LM Studio / Ollama / service instances on the LAN.
    Uses NetworkAutoConfig.discover_lan_agents() — TCP probe, no auth required.
    Mac-first: detects local subnet from the Mac IP, falls back to env hints.
    Note: full /24 scan takes ~10–30s; results are cached per request only.
    """
    if _net is None:
        return {"error": "network_autoconfig not available", "agents": {}}
    loop = asyncio.get_event_loop()
    # Run blocking scan in executor so we don't stall the event loop
    agents = await loop.run_in_executor(None, _net.discover_lan_agents)
    return {"timestamp": datetime.utcnow().isoformat(), "agents": agents}


@app.get("/", response_class=HTMLResponse)
async def root():
    """LAN dashboard HTML."""
    status = await api_status()

    ROLE_LABELS = {
        "perplexity_tools": ("PT", "router · budget gatekeeper · lifecycle owner"),
        "ultrathink":       ("US", "reasoning executor · stateless · 5-stage pipeline"),
        "lmstudio_mac":     ("MAC", "orchestrator · validator · Qwen3.5-9B-MLX-4bit · ctx 4096"),
        "lmstudio_win":     ("WIN", "agent(s) · coder/checker/refiner/executor/verifier · ctx 16384"),
        "ollama_mac":       ("MAC", "Ollama fallback · execution target when Win busy"),
        "ollama_win":       ("WIN", "Ollama primary · default execution target · win-rtx3080"),
    }

    def render_card(name, data):
        tag, role_text = ROLE_LABELS.get(name, ("", ""))
        tag_html = f'<span class="tag">{tag}</span>' if tag else ""

        if isinstance(data, list):
            dots = ""
            eps = ""
            for item in data:
                ok = item.get("ok", False)
                dot_color = "#a3e635" if ok else "#f87171"
                ep = item.get("endpoint", "?")
                dots += f'<span style="color:{dot_color};font-size:1.1rem;">●</span> '
                eps += f'<code style="font-size:0.78rem;">{ep}</code> '
            status_html = f'<span>{dots}</span><span style="color:#94a3b8;font-size:0.8rem;">{eps}</span>'
        else:
            ok = data.get("ok", False)
            dot_color = "#a3e635" if ok else "#f87171"
            state = "UP" if ok else "DOWN"
            ep = data.get("endpoint", "")
            ver = data.get("version", "")
            models = data.get("models", [])
            detail_parts = []
            if ep:
                detail_parts.append(f'<code style="font-size:0.78rem;">{ep}</code>')
            if ver:
                detail_parts.append(f'<span style="color:#94a3b8;font-size:0.78rem;">v{ver}</span>')
            if models:
                m_str = ", ".join(str(m) for m in models[:2])
                detail_parts.append(f'<span style="color:#94a3b8;font-size:0.75rem;">[{m_str}]</span>')
            detail_html = " &nbsp; ".join(detail_parts)
            status_html = (
                f'<span style="color:{dot_color};font-size:1.1rem;">●</span>'
                f'<span style="margin-left:0.4rem;font-weight:bold;">{state}</span>'
                f'<span style="margin-left:0.8rem;">{detail_html}</span>'
            )

        return (
            f'<div class="card">'
            f'  <div class="card-left">'
            f'    {tag_html}'
            f'    <span class="svc-name">{name}</span>'
            f'    <span class="role">{role_text}</span>'
            f'  </div>'
            f'  <div class="card-right">{status_html}</div>'
            f'</div>'
        )

    services_html = ""
    for name, data in status["services"].items():
        services_html += render_card(name, data)

    agents_hint = (
        '<div class="card hint-card">'
        '  <div class="card-left">'
        '    <span class="tag" style="background:#1e293b;">CFG</span>'
        '    <span class="svc-name">default model</span>'
        '    <span class="role">Ollama shared · all roles unless overridden</span>'
        '  </div>'
        '  <div class="card-right">'
        '    <code style="font-size:0.82rem;">qwen3.5:35b-a3b-q4&#95;K&#95;M</code>'
        '    &nbsp;·&nbsp;'
        '    <a href="/api/lan-agents" style="color:#7dd3fc;font-size:0.82rem;">discover LAN agents ↗</a>'
        '    &nbsp;·&nbsp;'
        '    <a href="/api/status" style="color:#7dd3fc;font-size:0.82rem;">JSON ↗</a>'
        '  </div>'
        '</div>'
    )

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <meta http-equiv="refresh" content="10">
        <title>ultrathink Portal v1.0 RC</title>
        <style>
            *, *::before, *::after {{ box-sizing: border-box; }}
            body {{
                background: #6b7280;
                color: #f5f5f0;
                font-family: 'Courier New', monospace;
                margin: 0;
                padding: 2rem 1rem;
                line-height: 1.5;
                font-size: 0.9rem;
            }}
            .container {{ max-width: 860px; margin: 0 auto; }}
            h1 {{
                margin: 0 0 0.25rem 0;
                font-size: 1.2rem;
                font-weight: normal;
                letter-spacing: 0.05em;
                color: #f5f5f0;
            }}
            .subtitle {{
                font-size: 0.78rem;
                color: #d1d5db;
                margin-bottom: 1.5rem;
                border-bottom: 1px solid #9ca3af;
                padding-bottom: 0.75rem;
            }}
            .section-label {{
                font-size: 0.72rem;
                text-transform: uppercase;
                letter-spacing: 0.1em;
                color: #d1d5db;
                margin: 1.2rem 0 0.4rem 0;
            }}
            .card {{
                background: #4b5563;
                border: 1px solid #9ca3af;
                padding: 0.6rem 0.9rem;
                margin: 0.3rem 0;
                border-radius: 3px;
                display: flex;
                justify-content: space-between;
                align-items: center;
                gap: 1rem;
            }}
            .hint-card {{ background: #374151; border-color: #6b7280; }}
            .card-left {{
                display: flex;
                align-items: center;
                gap: 0.5rem;
                flex-wrap: wrap;
                min-width: 0;
            }}
            .card-right {{
                display: flex;
                align-items: center;
                gap: 0.4rem;
                flex-shrink: 0;
                flex-wrap: wrap;
            }}
            .tag {{
                background: #374151;
                color: #d1d5db;
                font-size: 0.68rem;
                padding: 0.1rem 0.4rem;
                border-radius: 2px;
                letter-spacing: 0.08em;
                border: 1px solid #6b7280;
            }}
            .svc-name {{ font-weight: bold; color: #f5f5f0; }}
            .role {{ color: #d1d5db; font-size: 0.75rem; }}
            .timestamp {{
                margin-top: 1.5rem;
                font-size: 0.75rem;
                color: #d1d5db;
                border-top: 1px solid #9ca3af;
                padding-top: 0.75rem;
            }}
            a {{ color: #7dd3fc; text-decoration: none; }}
            a:hover {{ text-decoration: underline; }}
            code {{ color: #e2e8f0; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>ultrathink · v1.0 RC</h1>
            <div class="subtitle">
                orchestrator: <strong>mac-studio</strong>
                &nbsp;·&nbsp;
                execution: <strong>win-rtx3080</strong> (primary) / mac-studio (fallback)
                &nbsp;·&nbsp;
                <a href="/api/status">JSON status</a>
                &nbsp;·&nbsp;
                <a href="/api/lan-agents">LAN scan</a>
            </div>

            <div class="section-label">services</div>
            {services_html}

            <div class="section-label">config</div>
            {agents_hint}

            <div class="timestamp">
                {status['timestamp']} UTC &nbsp;·&nbsp; auto-refresh 10s
            </div>
        </div>
    </body>
    </html>
    """

    return html


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=PORTAL_HOST, port=PORTAL_PORT)
