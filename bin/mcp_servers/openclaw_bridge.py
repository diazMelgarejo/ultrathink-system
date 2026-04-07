"""
openclaw_bridge.py — async HTTP bridge for the OpenClaw gateway.

Replaces multi_agent/mcp_servers/lmstudio_bridge.py. Same Python interface,
different backend. All model calls are routed through the OpenClaw gateway
at 127.0.0.1:18789 (OpenAI-compatible). The agent_id field maps to an agent
declared in ~/.openclaw/openclaw.json; OpenClaw resolves it to the correct
provider (LM Studio / Ollama) and hardware (Mac / Windows).

Usage:
    from bin.mcp_servers.openclaw_bridge import chat, health, list_models

    result = await chat("orchestrator", "Decompose this task...")
    ok     = await health()
    agents = await list_models()
"""
from __future__ import annotations

import os
from typing import Optional

import httpx

OPENCLAW_GATEWAY = os.getenv("OPENCLAW_GATEWAY", "http://127.0.0.1:18789")
OPENCLAW_TIMEOUT = int(os.getenv("OPENCLAW_TIMEOUT", "120"))


async def chat(
    agent_id: str,
    input_text: str,
    context_length: int = 4096,
    # Legacy keyword args accepted for drop-in compat with lmstudio_bridge callers
    endpoint: Optional[str] = None,
    model: Optional[str] = None,
    token: Optional[str] = None,
    integrations: Optional[list] = None,
    **_kwargs,
) -> dict:
    """
    Send a chat request through the OpenClaw gateway.

    Args:
        agent_id: OpenClaw agent ID (e.g. "orchestrator", "coder", "mac-researcher").
                  OpenClaw resolves this to the correct provider and model.
        input_text: Prompt / task description.
        context_length: max_tokens for the response (default 4096).

    Returns:
        {
            "content": str,
            "tokens": int,
            "model": str,
            "endpoint": str,
            "metadata": dict
        }
    """
    payload = {
        "model": agent_id,
        "messages": [{"role": "user", "content": input_text}],
        "stream": False,
        "max_tokens": context_length,
    }
    async with httpx.AsyncClient(timeout=OPENCLAW_TIMEOUT) as client:
        try:
            r = await client.post(
                f"{OPENCLAW_GATEWAY}/v1/chat/completions",
                json=payload,
                headers={"Content-Type": "application/json"},
            )
            r.raise_for_status()
            result = r.json()
            choices = result.get("choices", [])
            content = choices[0]["message"]["content"] if choices else ""
            return {
                "content": content,
                "tokens": result.get("usage", {}).get("total_tokens", 0),
                "model": result.get("model", agent_id),
                "endpoint": OPENCLAW_GATEWAY,
                "metadata": {
                    "id": result.get("id"),
                    "agent_id": agent_id,
                    "created": result.get("created"),
                },
            }
        except (httpx.RequestError, httpx.HTTPStatusError) as e:
            raise RuntimeError(
                f"OpenClaw chat failed for agent '{agent_id}': {e}"
            )


async def list_models(agent_id: str = "", **_) -> list[str]:
    """
    List agents/models available from the OpenClaw gateway.
    Returns list of agent IDs registered in ~/.openclaw/openclaw.json.
    """
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            r = await client.get(f"{OPENCLAW_GATEWAY}/v1/models")
            r.raise_for_status()
            return [m.get("id") for m in r.json().get("data", [])]
        except (httpx.RequestError, httpx.HTTPStatusError) as e:
            raise RuntimeError(f"Failed to list OpenClaw agents: {e}")


async def health(endpoint: str = "", token: str = "", **_) -> bool:
    """
    Check if the OpenClaw gateway is reachable and healthy.
    Returns True if port 18789 is responding, False otherwise.
    """
    async with httpx.AsyncClient(timeout=5) as client:
        try:
            r = await client.get(f"{OPENCLAW_GATEWAY}/health")
            return r.status_code == 200
        except (httpx.RequestError, httpx.HTTPStatusError):
            return False
