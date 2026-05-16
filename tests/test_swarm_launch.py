#!/usr/bin/env python3
"""Tests for fail-closed swarm launch."""
from __future__ import annotations

from fastapi.testclient import TestClient

import portal_server


class _FakeResponse:
    def __init__(self, payload, status_code: int = 200):
        self._payload = payload
        self.status_code = status_code

    def json(self):
        return self._payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


class _FakeLaunchClient:
    submitted = []
    fail_role = None

    def __init__(self, *args, **kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def post(self, url: str, json=None, **kwargs):
        if url.endswith("/models/route"):
            return _FakeResponse({"backend_hint": "lmstudio-mac"})
        if url.endswith("/v1/jobs"):
            self.submitted.append(json)
            role = json["metadata"]["role"]
            if role == self.fail_role:
                raise RuntimeError("dispatch failed")
            return _FakeResponse({"job_id": f"job-{role}"})
        raise AssertionError(f"unexpected POST {url}")


def _portal_status(ok=True):
    return {
        "hardware_policy": {
            "ok": ok,
            "violations": [] if ok else ["NEVER_MAC bad-model advertised by lmstudio-mac"],
            "safe_defaults": {"mac": ["mac-model"], "win": []},
        }
    }


def test_swarm_launch_requires_approval(monkeypatch):
    async def fake_api_status():
        return _portal_status()

    monkeypatch.setattr(portal_server, "api_status", fake_api_status)
    with TestClient(portal_server.app, raise_server_exceptions=True) as client:
        response = client.post("/api/swarm/launch", json={"objective": "Ship launch"})

    assert response.status_code == 422


def test_swarm_launch_blocks_on_hardware_policy(monkeypatch):
    async def fake_api_status():
        return _portal_status(ok=False)

    monkeypatch.setattr(portal_server, "api_status", fake_api_status)
    _FakeLaunchClient.submitted = []
    _FakeLaunchClient.fail_role = None
    monkeypatch.setattr(portal_server.httpx, "AsyncClient", _FakeLaunchClient)

    with TestClient(portal_server.app, raise_server_exceptions=False) as client:
        response = client.post(
            "/api/swarm/launch",
            json={"objective": "Ship launch", "approved": True},
        )

    assert response.status_code == 409
    assert response.json()["detail"]["blocked"] is True
    assert _FakeLaunchClient.submitted == []


def test_swarm_launch_submits_metadata_compatible_pt_jobs(monkeypatch):
    async def fake_api_status():
        return _portal_status()

    monkeypatch.setattr(portal_server, "api_status", fake_api_status)
    _FakeLaunchClient.submitted = []
    _FakeLaunchClient.fail_role = None
    monkeypatch.setattr(portal_server.httpx, "AsyncClient", _FakeLaunchClient)

    with TestClient(portal_server.app, raise_server_exceptions=True) as client:
        response = client.post(
            "/api/swarm/launch",
            json={"objective": "Ship launch", "approved": True},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["accepted"] is True
    assert len(body["accepted_jobs"]) == 5
    first = _FakeLaunchClient.submitted[0]
    assert set(first) == {"intent", "prompt", "backend_hint", "constraints", "metadata"}
    assert first["metadata"]["role"] == "context-agent"
    assert first["metadata"]["artifact_policy"] == "summary_and_refs_only"


def test_swarm_launch_returns_partial_dispatch_failure(monkeypatch):
    async def fake_api_status():
        return _portal_status()

    monkeypatch.setattr(portal_server, "api_status", fake_api_status)
    _FakeLaunchClient.submitted = []
    _FakeLaunchClient.fail_role = "verifier-agent"
    monkeypatch.setattr(portal_server.httpx, "AsyncClient", _FakeLaunchClient)

    with TestClient(portal_server.app, raise_server_exceptions=True) as client:
        response = client.post(
            "/api/swarm/launch",
            json={"objective": "Ship launch", "approved": True},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["accepted"] is False
    assert body["failed_jobs"][0]["role"] == "verifier-agent"
    assert len(body["accepted_jobs"]) == 4
