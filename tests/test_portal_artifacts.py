#!/usr/bin/env python3
"""Tests for safe artifact index responses."""
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


class _FakeArtifactClient:
    payload = {}
    status_code = 200

    def __init__(self, *args, **kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def get(self, url: str, **kwargs):
        return _FakeResponse(self.payload, self.status_code)


def test_artifacts_returns_artifact_refs(monkeypatch):
    _FakeArtifactClient.status_code = 200
    _FakeArtifactClient.payload = {
        "id": "job-1",
        "result": {
            "summary": "Implemented safely.",
            "artifacts": [{"path": "reports/summary.md", "mime_type": "text/markdown"}],
            "verification": {"findings": []},
            "replay_instructions": "Replay from preview payload.",
        },
    }
    monkeypatch.setattr(portal_server.httpx, "AsyncClient", _FakeArtifactClient)

    with TestClient(portal_server.app, raise_server_exceptions=True) as client:
        response = client.get("/api/jobs/job-1/artifacts")

    body = response.json()
    assert response.status_code == 200
    assert body["available"] is True
    assert body["artifacts"][0]["path"] == "reports/summary.md"
    assert body["summaries"][0]["text"] == "Implemented safely."


def test_artifacts_redacts_raw_transcript_fields(monkeypatch):
    _FakeArtifactClient.status_code = 200
    _FakeArtifactClient.payload = {
        "id": "job-1",
        "result": {
            "summary": "Safe summary.",
            "raw_transcript": "do not expose",
            "tool_traces": [{"name": "hidden"}],
        },
    }
    monkeypatch.setattr(portal_server.httpx, "AsyncClient", _FakeArtifactClient)

    with TestClient(portal_server.app, raise_server_exceptions=True) as client:
        response = client.get("/api/jobs/job-1/artifacts")

    body = response.json()
    assert "result.raw_transcript" in body["redacted_fields"]
    assert "result.tool_traces" in body["redacted_fields"]
    assert "do not expose" not in str(body)


def test_artifacts_handles_missing_result(monkeypatch):
    _FakeArtifactClient.status_code = 200
    _FakeArtifactClient.payload = {"id": "job-1", "status": "queued"}
    monkeypatch.setattr(portal_server.httpx, "AsyncClient", _FakeArtifactClient)

    with TestClient(portal_server.app, raise_server_exceptions=True) as client:
        response = client.get("/api/jobs/job-1/artifacts")

    body = response.json()
    assert response.status_code == 200
    assert body["artifacts"] == []
    assert body["summaries"] == []


def test_artifacts_handles_pt_404(monkeypatch):
    _FakeArtifactClient.status_code = 404
    _FakeArtifactClient.payload = {"detail": "missing"}
    monkeypatch.setattr(portal_server.httpx, "AsyncClient", _FakeArtifactClient)

    with TestClient(portal_server.app, raise_server_exceptions=True) as client:
        response = client.get("/api/jobs/missing/artifacts")

    body = response.json()
    assert response.status_code == 200
    assert body["available"] is False
    assert body["artifacts"] == []
    assert body["error"]
