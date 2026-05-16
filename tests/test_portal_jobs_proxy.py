#!/usr/bin/env python3
"""Tests for PT job proxy routes."""
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


class _FakeJobsClient:
    fail = False
    calls = []

    def __init__(self, *args, **kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def get(self, url: str, **kwargs):
        self.calls.append(("GET", url, kwargs))
        if self.fail:
            raise RuntimeError("pt down")
        if url.endswith("/v1/jobs"):
            return _FakeResponse({"jobs": [{"id": "job-1"}]})
        if url.endswith("/v1/jobs/job-1"):
            return _FakeResponse({"id": "job-1", "status": "running"})
        raise AssertionError(f"unexpected GET {url}")

    async def post(self, url: str, json=None, **kwargs):
        self.calls.append(("POST", url, json))
        if self.fail:
            raise RuntimeError("pt down")
        return _FakeResponse({"ok": True, "job_id": json["job_id"]})


def test_jobs_proxy_lists_pt_jobs(monkeypatch):
    _FakeJobsClient.fail = False
    _FakeJobsClient.calls = []
    monkeypatch.setattr(portal_server.httpx, "AsyncClient", _FakeJobsClient)

    with TestClient(portal_server.app, raise_server_exceptions=True) as client:
        response = client.get("/api/jobs")

    assert response.status_code == 200
    assert response.json()["jobs"] == [{"id": "job-1"}]


def test_jobs_proxy_gets_detail(monkeypatch):
    _FakeJobsClient.fail = False
    _FakeJobsClient.calls = []
    monkeypatch.setattr(portal_server.httpx, "AsyncClient", _FakeJobsClient)

    with TestClient(portal_server.app, raise_server_exceptions=True) as client:
        response = client.get("/api/jobs/job-1")

    assert response.status_code == 200
    assert response.json()["job"]["status"] == "running"


def test_jobs_proxy_cancel_posts_to_pt(monkeypatch):
    _FakeJobsClient.fail = False
    _FakeJobsClient.calls = []
    monkeypatch.setattr(portal_server.httpx, "AsyncClient", _FakeJobsClient)

    with TestClient(portal_server.app, raise_server_exceptions=True) as client:
        response = client.post("/api/jobs/job-1/cancel")

    assert response.status_code == 200
    assert response.json()["result"]["ok"] is True
    assert _FakeJobsClient.calls[0] == ("POST", f"{portal_server.PT_URL}/cancel", {"job_id": "job-1"})


def test_jobs_proxy_replay_posts_to_pt(monkeypatch):
    _FakeJobsClient.fail = False
    _FakeJobsClient.calls = []
    monkeypatch.setattr(portal_server.httpx, "AsyncClient", _FakeJobsClient)

    with TestClient(portal_server.app, raise_server_exceptions=True) as client:
        response = client.post("/api/jobs/job-1/replay")

    assert response.status_code == 200
    assert response.json()["result"]["job_id"] == "job-1"
    assert _FakeJobsClient.calls[0] == ("POST", f"{portal_server.PT_URL}/replay", {"job_id": "job-1"})


def test_jobs_proxy_handles_pt_down(monkeypatch):
    _FakeJobsClient.fail = True
    _FakeJobsClient.calls = []
    monkeypatch.setattr(portal_server.httpx, "AsyncClient", _FakeJobsClient)

    with TestClient(portal_server.app, raise_server_exceptions=True) as client:
        response = client.get("/api/jobs")

    assert response.status_code == 200
    body = response.json()
    assert body["available"] is False
    assert body["jobs"] == []
    assert body["error"]
