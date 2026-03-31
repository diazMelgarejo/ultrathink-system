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


@app.get("/", response_class=HTMLResponse)
async def root():
    """LAN dashboard HTML."""
    status = await api_status()

    # Helper to render service status
    def service_badge(service_data):
        if isinstance(service_data, list):
            # lmstudio_win is array
            badges = ""
            for item in service_data:
                ok = item.get("ok", False)
                color = "#4ade80" if ok else "#f87171"
                ep = item.get("endpoint", "?")
                badges += f'<span style="color:{color};">● {ep}</span> '
            return badges
        else:
            ok = service_data.get("ok", False)
            color = "#4ade80" if ok else "#f87171"
            return f'<span style="color:{color};">●</span> {ok}'

    services_html = ""
    for name, data in status["services"].items():
        badge = service_badge(data)
        services_html += f'<div class="card"><strong>{name}</strong> {badge}</div>'

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <meta http-equiv="refresh" content="10">
        <title>ultrathink Portal v1.0 RC</title>
        <style>
            body {{
                background: #475569;
                color: #f8fafc;
                font-family: 'Courier New', monospace;
                margin: 0;
                padding: 2rem;
                line-height: 1.6;
            }}
            .container {{
                max-width: 800px;
                margin: 0 auto;
            }}
            h1 {{
                margin-top: 0;
                font-size: 1.5rem;
                border-bottom: 1px solid #64748b;
                padding-bottom: 1rem;
            }}
            .card {{
                background: #334155;
                border: 1px solid #64748b;
                padding: 1rem;
                margin: 0.5rem 0;
                border-radius: 4px;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }}
            .ok {{ color: #4ade80; }}
            .err {{ color: #f87171; }}
            .role {{ color: #94a3b8; font-size: 0.85rem; }}
            .timestamp {{
                margin-top: 2rem;
                font-size: 0.85rem;
                color: #94a3b8;
                border-top: 1px solid #64748b;
                padding-top: 1rem;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>ultrathink Portal v1.0 RC</h1>
            <p>Orchestrator: <span class="role">Mac Studio</span></p>
            <div>
                {services_html}
            </div>
            <div class="timestamp">
                Last updated: {status['timestamp']}<br>
                (Auto-refresh: 10s)
            </div>
        </div>
    </body>
    </html>
    """

    return html


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=PORTAL_HOST, port=PORTAL_PORT)
