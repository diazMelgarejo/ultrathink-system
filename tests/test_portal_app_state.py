#!/usr/bin/env python3
"""Tests for portal operator app state aggregation."""
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


class _FakeAsyncClient:
    responses = {}
    failures = set()

    def __init__(self, *args, **kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def get(self, url: str, **kwargs):
        path = "/" + url.split("/", 3)[3] if "://" in url else url
        if path in self.failures:
            raise RuntimeError(f"boom: {path}")
        return _FakeResponse(self.responses.get(path, {}))


def _portal_status(supervisor_jobs=None):
    return {
        "portal_version": "test",
        "services": {"perplexity_tools": {"ok": True}},
        "routing": {"gateway_ready": True},
        "hardware_policy": {"ok": True, "violations": []},
        "tools": {"gemini-cli": {"ok": True}},
        "supervisor_jobs": supervisor_jobs or [],
    }


def test_app_state_contains_real_sections(monkeypatch):
    async def fake_api_status():
        return _portal_status()

    monkeypatch.setattr(portal_server, "api_status", fake_api_status)
    _FakeAsyncClient.failures = set()
    _FakeAsyncClient.responses = {
        "/runtime": {"gateway": {"ready": True}},
        "/models": {"models": [{"id": "qwen"}]},
        "/activity?limit=25": {"events": [{"id": "evt-1"}]},
        "/v1/jobs": {"jobs": [{"id": "job-1", "status": "running"}]},
    }
    monkeypatch.setattr(portal_server.httpx, "AsyncClient", _FakeAsyncClient)

    with TestClient(portal_server.app, raise_server_exceptions=True) as client:
        response = client.get("/api/app/state")

    assert response.status_code == 200
    body = response.json()
    assert body["portal"]["available"] is True
    assert body["runtime"]["available"] is True
    assert body["models"]["data"]["models"][0]["id"] == "qwen"
    assert body["activity"]["data"]["events"][0]["id"] == "evt-1"
    assert body["jobs"]["data"]["jobs"][0]["id"] == "job-1"


def test_app_state_uses_supervisor_jobs_fallback(monkeypatch):
    async def fake_api_status():
        return _portal_status(supervisor_jobs=[{"id": "fallback-job"}])

    monkeypatch.setattr(portal_server, "api_status", fake_api_status)
    _FakeAsyncClient.failures = {"/v1/jobs"}
    _FakeAsyncClient.responses = {
        "/runtime": {},
        "/models": {},
        "/activity?limit=25": {"events": []},
    }
    monkeypatch.setattr(portal_server.httpx, "AsyncClient", _FakeAsyncClient)

    with TestClient(portal_server.app, raise_server_exceptions=True) as client:
        response = client.get("/api/app/state")

    assert response.status_code == 200
    body = response.json()
    assert body["jobs"]["source"] == "portal:supervisor_jobs_fallback"
    assert body["jobs"]["available"] is True
    assert body["jobs"]["data"]["jobs"] == [{"id": "fallback-job"}]


def test_app_state_reports_pt_partial_failure(monkeypatch):
    async def fake_api_status():
        return _portal_status()

    monkeypatch.setattr(portal_server, "api_status", fake_api_status)
    _FakeAsyncClient.failures = {"/runtime", "/models"}
    _FakeAsyncClient.responses = {
        "/activity?limit=25": {"events": []},
        "/v1/jobs": {"jobs": []},
    }
    monkeypatch.setattr(portal_server.httpx, "AsyncClient", _FakeAsyncClient)

    with TestClient(portal_server.app, raise_server_exceptions=True) as client:
        response = client.get("/api/app/state")

    assert response.status_code == 200
    body = response.json()
    assert body["portal"]["data"]["services"]["perplexity_tools"]["ok"] is True
    assert body["runtime"]["available"] is False
    assert body["runtime"]["error"]
    assert body["models"]["available"] is False
