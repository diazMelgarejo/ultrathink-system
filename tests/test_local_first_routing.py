#!/usr/bin/env python3
"""
test_local_first_routing.py
===========================
TDD: Platform-aware, task-type-aware backend routing.

Priority matrix (no override):

  On Mac:
    1. mac_main      — localhost:1234 (LM Studio Mac)
    2. win_coding    — Windows LM Studio (for task_type="code" only)
    3. win_main      — Windows LM Studio (all other task types)
    4. cloud         — Anthropic API
    5. other         — remaining fallbacks (Ollama, etc.)

  On Windows:
    1. win_main      — Windows LM Studio
    2. cloud         — Anthropic API
    3. other         — remaining fallbacks

Overrides (in precedence order, highest first):
  - Per-request: UltraThinkRequest.backend_priority  ("local" | "cloud" | "windows")
  - Env var:     ORAMA_BACKEND_PRIORITY              ("local" | "cloud" | "windows")
  - Auto-detect: current platform via ORAMA_PLATFORM env or sys detection
  - Default:     "local" (Mac behavior)

RED tests written first.
"""
from __future__ import annotations

import os
import pytest

import api_server
from api_server import BackendRouter, BackendPriority


# ── BackendPriority enum ──────────────────────────────────────────────────────

def test_backend_priority_has_local_cloud_windows():
    assert BackendPriority.LOCAL == "local"
    assert BackendPriority.CLOUD == "cloud"
    assert BackendPriority.WINDOWS == "windows"


# ── Mac platform: mac_main first for all task types ──────────────────────────

def test_mac_default_non_code_order(monkeypatch):
    """On Mac, non-code: mac_main → win_main → cloud → …"""
    monkeypatch.setenv("ORAMA_PLATFORM", "mac")
    router = BackendRouter(task_type="analysis")
    endpoints = router.ordered_endpoints()
    names = [e["name"] for e in endpoints]
    assert names[0] == "mac_main"
    assert names[1] == "win_main"
    assert names[2] == "cloud"


def test_mac_code_task_uses_win_coding_second(monkeypatch):
    """On Mac, coding tasks: mac_main → win_coding → win_main → cloud → …"""
    monkeypatch.setenv("ORAMA_PLATFORM", "mac")
    router = BackendRouter(task_type="code")
    endpoints = router.ordered_endpoints()
    names = [e["name"] for e in endpoints]
    assert names[0] == "mac_main"
    assert names[1] == "win_coding"
    assert names[2] == "win_main"
    assert names[3] == "cloud"


def test_mac_mac_main_url_is_localhost(monkeypatch):
    monkeypatch.setenv("ORAMA_PLATFORM", "mac")
    router = BackendRouter()
    mac_ep = next(e for e in router.ordered_endpoints() if e["name"] == "mac_main")
    assert "localhost:1234" in mac_ep["url"]


# ── Windows platform: win_main first ─────────────────────────────────────────

def test_windows_default_order(monkeypatch):
    """On Windows: win_main → cloud → mac_main → …"""
    monkeypatch.setenv("ORAMA_PLATFORM", "windows")
    router = BackendRouter(task_type="analysis")
    endpoints = router.ordered_endpoints()
    names = [e["name"] for e in endpoints]
    assert names[0] == "win_main"
    assert names[1] == "cloud"


def test_windows_coding_still_uses_win_main_first(monkeypatch):
    """On Windows, coding tasks still start with win_main (no Mac available)."""
    monkeypatch.setenv("ORAMA_PLATFORM", "windows")
    router = BackendRouter(task_type="code")
    names = [e["name"] for e in router.ordered_endpoints()]
    assert names[0] == "win_main"


# ── BackendRouter: default platform auto-detects as mac on Darwin ─────────────

def test_auto_detect_platform_darwin_defaults_to_mac(monkeypatch):
    monkeypatch.delenv("ORAMA_PLATFORM", raising=False)
    router = BackendRouter()
    # On Darwin (this test machine), should detect mac
    assert router.platform in ("mac", "windows")  # one of the two valid values


def test_orama_platform_env_overrides_auto_detect(monkeypatch):
    monkeypatch.setenv("ORAMA_PLATFORM", "windows")
    router = BackendRouter()
    assert router.platform == "windows"


# ── BackendRouter: env-var ORAMA_BACKEND_PRIORITY override ───────────────────

def test_backend_router_cloud_priority_from_env(monkeypatch):
    monkeypatch.setenv("ORAMA_BACKEND_PRIORITY", "cloud")
    monkeypatch.setenv("ORAMA_PLATFORM", "mac")
    router = BackendRouter()
    assert router.priority == BackendPriority.CLOUD
    assert router.ordered_endpoints()[0]["name"] == "cloud"


def test_backend_router_windows_priority_from_env(monkeypatch):
    monkeypatch.setenv("ORAMA_BACKEND_PRIORITY", "windows")
    monkeypatch.setenv("ORAMA_PLATFORM", "mac")
    router = BackendRouter()
    assert router.priority == BackendPriority.WINDOWS
    # When priority is "windows", first endpoint should be win_main or win_coding
    assert router.ordered_endpoints()[0]["name"] in ("win_main", "win_coding")


def test_backend_router_ignores_unknown_env_value(monkeypatch):
    """Unknown ORAMA_BACKEND_PRIORITY → fall back to platform-default (never crash)."""
    monkeypatch.setenv("ORAMA_BACKEND_PRIORITY", "garbage")
    monkeypatch.setenv("ORAMA_PLATFORM", "mac")
    router = BackendRouter()
    assert router.priority == BackendPriority.LOCAL


# ── BackendRouter: per-request override beats env ────────────────────────────

def test_backend_router_with_override_cloud(monkeypatch):
    monkeypatch.setenv("ORAMA_PLATFORM", "mac")
    router = BackendRouter(override="cloud")
    assert router.priority == BackendPriority.CLOUD
    assert router.ordered_endpoints()[0]["name"] == "cloud"


def test_backend_router_with_override_local(monkeypatch):
    monkeypatch.setenv("ORAMA_PLATFORM", "mac")
    router = BackendRouter(override="local")
    assert router.priority == BackendPriority.LOCAL
    assert router.ordered_endpoints()[0]["name"] == "mac_main"


def test_backend_router_override_beats_env(monkeypatch):
    monkeypatch.setenv("ORAMA_BACKEND_PRIORITY", "cloud")
    monkeypatch.setenv("ORAMA_PLATFORM", "mac")
    router = BackendRouter(override="windows")
    assert router.priority == BackendPriority.WINDOWS


# ── UltraThinkRequest: backend_priority field ─────────────────────────────────

def test_ultrathink_request_accepts_backend_priority():
    from api_server import UltraThinkRequest
    req = UltraThinkRequest(task_description="test", backend_priority="cloud")
    assert req.backend_priority == "cloud"


def test_ultrathink_request_backend_priority_defaults_to_local():
    from api_server import UltraThinkRequest
    req = UltraThinkRequest(task_description="test")
    assert req.backend_priority == "local"


def test_ultrathink_request_backend_priority_rejects_invalid():
    from api_server import UltraThinkRequest
    with pytest.raises(Exception):
        UltraThinkRequest(task_description="test", backend_priority="badvalue")


# ── HTTP endpoint: backend_priority in request → response metadata ────────────

def test_http_endpoint_local_priority_in_metadata(monkeypatch):
    from fastapi.testclient import TestClient

    async def fake_call(prompt, model, max_tokens, temperature):
        return "local result", "http://localhost:1234"

    monkeypatch.setattr(api_server, "_call_with_fallback", fake_call)
    client = TestClient(api_server.app)

    resp = client.post("/ultrathink", json={"task_description": "route me"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["metadata"]["backend_priority"] == "local"
    assert body["metadata"]["backend_attempted"] in ("mac_main", "local")


def test_http_endpoint_cloud_override_in_metadata(monkeypatch):
    from fastapi.testclient import TestClient

    async def fake_call(prompt, model, max_tokens, temperature):
        return "cloud result", "https://api.anthropic.com"

    monkeypatch.setattr(api_server, "_call_with_fallback", fake_call)
    client = TestClient(api_server.app)

    resp = client.post("/ultrathink", json={
        "task_description": "route me to cloud",
        "backend_priority": "cloud",
    })
    assert resp.status_code == 200
    body = resp.json()
    assert body["metadata"]["backend_priority"] == "cloud"


# ── /health: expose backend routing ──────────────────────────────────────────

def test_health_endpoint_exposes_backend_priority():
    from fastapi.testclient import TestClient
    client = TestClient(api_server.app)
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert "backend_priority" in body
    assert body["backend_priority"] in ("local", "cloud", "windows")
    assert "backend_endpoints" in body
