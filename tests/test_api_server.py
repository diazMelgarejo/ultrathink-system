#!/usr/bin/env python3
"""
test_api_server.py
==================
Request/response tests for the HTTP bridge.
"""
from __future__ import annotations

import json
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
    assert body["pt_runtime"]["available"] is False


def test_runtime_state_reads_pt_payload(monkeypatch, tmp_path):
    runtime_path = tmp_path / "pt-runtime.json"
    runtime_path.write_text(
        json.dumps(
            {
                "gateway": {"gateway_ready": True},
                "routing": {"distributed": True},
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("PT_RUNTIME_STATE", str(runtime_path))

    with TestClient(api_server.app, raise_server_exceptions=True) as client:
        response = client.get("/runtime-state")

    assert response.status_code == 200
    body = response.json()
    assert body["available"] is True
    assert body["runtime"]["gateway"]["gateway_ready"] is True


def test_hardware_mismatch_mac_provider_with_windows_model(monkeypatch):
    """lmstudio-mac + Windows-only model → must return 400 HARDWARE_MISMATCH."""
    async def fake_call_with_fallback(prompt, model, max_tokens, temperature):
        return "should not reach here", "http://redacted"

    monkeypatch.setattr(api_server, "_call_with_fallback", fake_call_with_fallback)

    # Mock the resolver to raise HardwareAffinityError for NEVER_MAC models
    original_resolver = api_server._policy_resolver
    mock_resolver = type('MockResolver', (), {
        'initialize': lambda self: None,
        'check_affinity': lambda self, m, p: (
            None if p != "mac" or "qwen3.5-27b" not in m.lower()
            else (_ for _ in ()).throw(
                api_server.HardwareAffinityError(
                    f"[alphaclaw] Fatal: '{m}' is NEVER_MAC. Assign to lmstudio-win only."
                )
            )
        ),
        'expected_platform_for_model': lambda self, m: None,
        'source': 'mock',
        'pt_available': True,
    })()
    api_server._policy_resolver = mock_resolver

    try:
        with TestClient(api_server.app, raise_server_exceptions=True) as client:
            response = client.post(
                "/ultrathink",
                json={
                    "task_description": "Write a sorting algorithm",
                    "task_type": "code",
                    "model_hint": "lmstudio-mac/Qwen3.5-27B-Claude-4.6-Opus-Reasoning-Distilled-v2",
                },
            )

        assert response.status_code == 400
        body = response.json()
        assert body["error"] == "HARDWARE_MISMATCH"
        assert "NEVER_MAC" in body["detail"]
    finally:
        api_server._policy_resolver = original_resolver


def test_hardware_mismatch_win_provider_with_mac_model(monkeypatch):
    """lmstudio-win + Mac-only MLX model → must return 400 HARDWARE_MISMATCH."""
    async def fake_call_with_fallback(prompt, model, max_tokens, temperature):
        return "should not reach here", "http://redacted"

    monkeypatch.setattr(api_server, "_call_with_fallback", fake_call_with_fallback)

    # Mock the resolver to raise HardwareAffinityError for NEVER_WIN models
    original_resolver = api_server._policy_resolver
    mock_resolver = type('MockResolver', (), {
        'initialize': lambda self: None,
        'check_affinity': lambda self, m, p: (
            None if p != "win" or "qwen3.5-9b-mlx" not in m.lower()
            else (_ for _ in ()).throw(
                api_server.HardwareAffinityError(
                    f"[alphaclaw] Fatal: '{m}' is NEVER_WIN. Assign to lmstudio-mac only."
                )
            )
        ),
        'expected_platform_for_model': lambda self, m: None,
        'source': 'mock',
        'pt_available': True,
    })()
    api_server._policy_resolver = mock_resolver

    try:
        with TestClient(api_server.app, raise_server_exceptions=True) as client:
            response = client.post(
                "/ultrathink",
                json={
                    "task_description": "Run MLX inference",
                    "task_type": "code",
                    "model_hint": "lmstudio-win/Qwen3.5-9B-MLX-4bit",
                },
            )

        assert response.status_code == 400
        body = response.json()
        assert body["error"] == "HARDWARE_MISMATCH"
        assert "NEVER_WIN" in body["detail"]
    finally:
        api_server._policy_resolver = original_resolver


def test_fail_closed_when_perpetuatoolsroot_missing(monkeypatch):
    monkeypatch.delenv("PERPETUA_TOOLS_ROOT", raising=False)
    monkeypatch.delenv("PERPETUA_TOOLS_PATH", raising=False)

    original_resolver = api_server._policy_resolver
    mock_resolver = type("MockResolver", (), {
        "initialize": lambda self: None,
        "check_affinity": lambda self, m, p: None,
        "expected_platform_for_model": lambda self, m: None,
        "source": "disabled-no-cache",
        "pt_available": False,
    })()
    api_server._policy_resolver = mock_resolver

    try:
        with TestClient(api_server.app, raise_server_exceptions=True) as client:
            response = client.post(
                "/ultrathink",
                json={
                    "task_description": "Run routed check",
                    "task_type": "code",
                    "model_hint": "lmstudio-mac/any-model",
                },
            )
        assert response.status_code == 400
        body = response.json()
        assert body["error"] == "POLICY_UNAVAILABLE"
    finally:
        api_server._policy_resolver = original_resolver


def test_fail_closed_when_platform_and_provider_hint_both_present(monkeypatch):
    monkeypatch.delenv("PERPETUA_TOOLS_ROOT", raising=False)
    monkeypatch.delenv("PERPETUA_TOOLS_PATH", raising=False)

    original_resolver = api_server._policy_resolver
    mock_resolver = type("MockResolver", (), {
        "initialize": lambda self: None,
        "check_affinity": lambda self, m, p: None,
        "expected_platform_for_model": lambda self, m: None,
        "source": "disabled-no-cache",
        "pt_available": False,
    })()
    api_server._policy_resolver = mock_resolver

    try:
        with TestClient(api_server.app, raise_server_exceptions=True) as client:
            response = client.post(
                "/ultrathink",
                json={
                    "task_description": "Run routed check",
                    "task_type": "code",
                    "platform": "mac",
                    "model_hint": "lmstudio-mac/any-model",
                },
            )
        assert response.status_code == 400
        body = response.json()
        assert body["error"] == "POLICY_UNAVAILABLE"
    finally:
        api_server._policy_resolver = original_resolver


def test_fail_closed_when_only_legacy_path_env_is_set(monkeypatch):
    monkeypatch.delenv("PERPETUA_TOOLS_ROOT", raising=False)
    monkeypatch.setenv("PERPETUA_TOOLS_PATH", "/tmp/not-a-real-pt-root")

    original_resolver = api_server._policy_resolver
    mock_resolver = type("MockResolver", (), {
        "initialize": lambda self: None,
        "check_affinity": lambda self, m, p: None,
        "expected_platform_for_model": lambda self, m: None,
        "source": "disabled-no-cache",
        "pt_available": False,
    })()
    api_server._policy_resolver = mock_resolver

    try:
        with TestClient(api_server.app, raise_server_exceptions=True) as client:
            response = client.post(
                "/ultrathink",
                json={
                    "task_description": "Run routed check",
                    "task_type": "code",
                    "model_hint": "lmstudio-win/any-model",
                },
            )
        assert response.status_code == 400
        assert response.json()["error"] == "POLICY_UNAVAILABLE"
    finally:
        api_server._policy_resolver = original_resolver
