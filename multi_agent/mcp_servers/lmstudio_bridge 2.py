"""
LM Studio async HTTP bridge — thin transport layer for Mac + Windows orchestration.
Env-backed configuration, no orchestration logic. Context-aware for both endpoints.
"""
import os
import httpx
from typing import Optional

# === ENV CONFIGURATION ===
LMS_WIN_ENDPOINTS = [
    s.strip() for s in os.getenv(
        "LM_STUDIO_WIN_ENDPOINTS", "http://192.168.1.100:1234"
    ).split(",")
]
LMS_MAC_ENDPOINT = os.getenv("LM_STUDIO_MAC_ENDPOINT", "http://localhost:1234")
LMS_API_TOKEN = os.getenv("LM_STUDIO_API_TOKEN", "")
LMS_TIMEOUT = int(os.getenv("LM_STUDIO_TIMEOUT", "120"))
LMS_WIN_MAX_PARALLEL = int(os.getenv("LMS_WIN_MAX_PARALLEL", "4"))


async def list_models(endpoint: str, token: str = "") -> list[str]:
    """
    Fetch available models from LM Studio /v1/models endpoint.
    Returns list of model IDs (names).
    """
    async with httpx.AsyncClient(timeout=LMS_TIMEOUT) as client:
        try:
            headers = {"Authorization": f"Bearer {token}"} if token else {}
            response = await client.get(f"{endpoint}/v1/models", headers=headers)
            response.raise_for_status()
            data = response.json()
            return [m.get("id") for m in data.get("data", [])]
        except (httpx.RequestError, httpx.HTTPStatusError) as e:
            raise RuntimeError(f"Failed to fetch models from {endpoint}: {e}")


async def chat(
    endpoint: str,
    model: str,
    input_text: str,
    context_length: int = 4096,
    integrations: list = None,
    token: str = "",
) -> dict:
    """
    Send chat request to LM Studio /api/v1/chat endpoint.
    Returns dict with extracted first message-type content, token count, and metadata.

    Args:
        endpoint: LM Studio base URL (e.g., http://localhost:1234)
        model: Model name/ID (e.g., Qwen3.5-9B-MLX-4bit)
        input_text: Prompt/task description
        context_length: Max tokens for response (default 4096)
        integrations: Optional list of integration configs
        token: Optional API token

    Returns:
        {
            "content": str,  # extracted message text
            "tokens": int,
            "model": str,
            "endpoint": str,
            "metadata": dict
        }
    """
    if integrations is None:
        integrations = []

    payload = {
        "model": model,
        "messages": [{"role": "user", "content": input_text}],
        "stream": False,
        "max_tokens": context_length,
    }

    async with httpx.AsyncClient(timeout=LMS_TIMEOUT) as client:
        try:
            headers = {"Content-Type": "application/json"}
            if token:
                headers["Authorization"] = f"Bearer {token}"

            response = await client.post(
                f"{endpoint}/api/v1/chat", json=payload, headers=headers
            )
            response.raise_for_status()
            result = response.json()

            # Extract first message-type content from output
            output = result.get("output", [])
            content = ""
            for item in output:
                if item.get("type") == "message":
                    content = item.get("content", "")
                    break

            return {
                "content": content,
                "tokens": result.get("tokens", 0),
                "model": model,
                "endpoint": endpoint,
                "metadata": {
                    "id": result.get("id"),
                    "created": result.get("created"),
                    "output_count": len(output),
                },
            }
        except (httpx.RequestError, httpx.HTTPStatusError) as e:
            raise RuntimeError(
                f"Chat request failed to {endpoint} with model {model}: {e}"
            )


async def health(endpoint: str, token: str = "") -> bool:
    """
    Check health of LM Studio endpoint.
    Returns True if reachable and responding, False otherwise.
    """
    async with httpx.AsyncClient(timeout=5) as client:
        try:
            headers = {"Authorization": f"Bearer {token}"} if token else {}
            response = await client.get(f"{endpoint}/v1/models", headers=headers)
            return response.status_code == 200
        except (httpx.RequestError, httpx.HTTPStatusError):
            return False
