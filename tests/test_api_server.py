#!/usr/bin/env python3
"""
test_api_server.py
==================
Request/response tests for the HTTP bridge.
"""
from __future__ import annotations

from fastapi.testclient import TestClient

import api_server
from bin.shared.bridge_contract import (
    optimize_for_to_reasoning_depth,
    reasoning_depth_to_optimize_for,
)


class _FakeHTTPResponse:
    def __init__(self, status_code: int):
        self.status_code = status_code


class _FakeAsyncClient:
    def __init__(self, *args, **kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def get(self, url: str, **kwargs):
        return _FakeHTTPResponse(200)

    async def post(self, url: str, **kwargs):
        return _FakeHTTPResponse(200)


def test_optimize_for_to_reasoning_depth_mapping_is_exact():
    assert optimize_for_to_reasoning_depth("reliability") == "ultra"
    assert optimize_for_to_reasoning_depth("creativity") == "deep"
    assert optimize_for_to_reasoning_depth("speed") == "standard"

    assert reasoning_depth_to_optimize_for("ultra").value == "reliability"
    assert reasoning_depth_to_optimize_for("deep").value == "creativity"
    assert reasoning_depth_to_optimize_for("standard").value == "speed"


def test_http_bridge_maps_optimize_for_to_reasoning_depth(monkeypatch):
    captured = {}

    async def fake_call_with_fallback(prompt, model, max_tokens, temperature):
        captured["prompt"] = prompt
        captured["model"] = model
        captured["max_tokens"] = max_tokens
        captured["temperature"] = temperature
        return "mapped output", "http://redacted"

    monkeypatch.setattr(api_server, "_call_with_fallback", fake_call_with_fallback)

    with TestClient(api_server.app, raise_server_exceptions=True) as client:
        response = client.post(
            "/ultrathink",
            json={
                "task_description": "Design a resilient orchestration layer",
                "optimize_for": "reliability",
                "task_type": "planning",
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["result"] == "mapped output"
    assert body["reasoning_depth"] == "ultra"
    assert body["model_used"] == api_server.DEFAULT_MODEL
    assert body["metadata"]["mapped_optimize_for"] == "reliability"
    assert body["metadata"]["mapping_source"] == "optimize_for"
    assert body["metadata"]["bridge_mode"] == "http_primary"
    assert "ultra-depth reasoning" in captured["prompt"]


def test_http_bridge_prefers_explicit_reasoning_depth(monkeypatch):
    async def fake_call_with_fallback(prompt, model, max_tokens, temperature):
        return "explicit depth output", "http://redacted"

    monkeypatch.setattr(api_server, "_call_with_fallback", fake_call_with_fallback)

    with TestClient(api_server.app, raise_server_exceptions=True) as client:
        response = client.post(
            "/ultrathink",
            json={
                "task_description": "Review a code migration plan",
                "reasoning_depth": "standard",
                "optimize_for": "reliability",
                "task_type": "planning",
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["reasoning_depth"] == "standard"
    assert body["model_used"] == api_server.FAST_MODEL
    assert body["metadata"]["mapped_optimize_for"] == "speed"
    assert body["metadata"]["mapping_source"] == "reasoning_depth"


def test_http_bridge_preserves_legacy_default_reasoning_depth(monkeypatch):
    async def fake_call_with_fallback(prompt, model, max_tokens, temperature):
        return "legacy default output", "http://redacted"

    monkeypatch.setattr(api_server, "_call_with_fallback", fake_call_with_fallback)

    with TestClient(api_server.app, raise_server_exceptions=True) as client:
        response = client.post(
            "/ultrathink",
            json={
                "task_description": "Analyze a backup path",
                "task_type": "analysis",
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["reasoning_depth"] == "standard"
    assert body["model_used"] == api_server.FAST_MODEL
    assert body["metadata"]["mapped_optimize_for"] == "speed"
    assert body["metadata"]["mapping_source"] == "default"


def test_http_bridge_honors_model_hint(monkeypatch):
    captured = {}

    async def fake_call_with_fallback(prompt, model, max_tokens, temperature):
        captured["model"] = model
        return "hinted output", "http://redacted"

    monkeypatch.setattr(api_server, "_call_with_fallback", fake_call_with_fallback)

    with TestClient(api_server.app, raise_server_exceptions=True) as client:
        response = client.post(
            "/ultrathink",
            json={
                "task_description": "Analyze failover design",
                "task_type": "analysis",
                "model_hint": "custom-model",
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["result"] == "hinted output"
    assert body["model_used"] == "custom-model"
    assert body["metadata"]["model_hint_used"] is True
    assert captured["model"] == "custom-model"


def test_http_health_endpoint(monkeypatch):
    monkeypatch.setattr(api_server.httpx, "AsyncClient", _FakeAsyncClient)

    with TestClient(api_server.app, raise_server_exceptions=True) as client:
        response = client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["lmstudio_win_reachable"] is True
    assert body["lmstudio_mac_reachable"] is True
    assert body["ollama_primary_reachable"] is True
    assert body["ollama_fallback_reachable"] is True
    assert body["bridge_mode"] == "http_primary"
    assert body["orchestrator"] == "mac-studio"
    assert body["execution_target"] == "win-rtx3080"
    assert body["primary_contract"] == "lmstudio"
    assert body["mapping"] == {
        "reliability": "ultra",
        "creativity": "deep",
        "speed": "standard",
    }
