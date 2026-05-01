#!/usr/bin/env python3
"""
test_v2_shape.py
================
TDD backport: wire orama-system v0.9.9.8 API models to match the v2 external
shape defined in orama-system/docs/v2/01-kernel-spec.md.

RED tests written first — each will fail until api_server.py is updated.
"""
from __future__ import annotations

import pytest
from pydantic import ValidationError

import api_server
from api_server import UltraThinkRequest, UltraThinkResponse


# ── session_id on request ─────────────────────────────────────────────────────

def test_ultrathink_request_accepts_session_id():
    req = UltraThinkRequest(task_description="hello", session_id="abc-123")
    assert req.session_id == "abc-123"


def test_ultrathink_request_session_id_defaults_to_none():
    req = UltraThinkRequest(task_description="hello")
    assert req.session_id is None


# ── session_id on response ────────────────────────────────────────────────────

def test_ultrathink_response_accepts_session_id():
    resp = UltraThinkResponse(
        status="success",
        result="ok",
        model_used="some-model",
        execution_time_ms=42,
        reasoning_depth="deep",
        metadata={},
        session_id="abc-123",
    )
    assert resp.session_id == "abc-123"


def test_ultrathink_response_session_id_defaults_to_none():
    resp = UltraThinkResponse(
        status="success",
        result="ok",
        model_used="some-model",
        execution_time_ms=42,
        reasoning_depth="deep",
        metadata={},
    )
    assert resp.session_id is None


# ── nodes_visited on response ─────────────────────────────────────────────────

def test_ultrathink_response_accepts_nodes_visited():
    resp = UltraThinkResponse(
        status="success",
        result="ok",
        model_used="some-model",
        execution_time_ms=42,
        reasoning_depth="deep",
        metadata={},
        nodes_visited=["route_node", "dispatch_node"],
    )
    assert resp.nodes_visited == ["route_node", "dispatch_node"]


def test_ultrathink_response_nodes_visited_defaults_to_empty_list():
    resp = UltraThinkResponse(
        status="success",
        result="ok",
        model_used="some-model",
        execution_time_ms=42,
        reasoning_depth="deep",
        metadata={},
    )
    assert resp.nodes_visited == []


# ── retry_count on response ───────────────────────────────────────────────────

def test_ultrathink_response_accepts_retry_count():
    resp = UltraThinkResponse(
        status="success",
        result="ok",
        model_used="some-model",
        execution_time_ms=42,
        reasoning_depth="deep",
        metadata={},
        retry_count=2,
    )
    assert resp.retry_count == 2


def test_ultrathink_response_retry_count_defaults_to_zero():
    resp = UltraThinkResponse(
        status="success",
        result="ok",
        model_used="some-model",
        execution_time_ms=42,
        reasoning_depth="deep",
        metadata={},
    )
    assert resp.retry_count == 0


# ── no pydantic protected-namespace warning for model_hint / model_used ───────

def test_ultrathink_request_no_model_hint_namespace_warning(recwarn):
    UltraThinkRequest(task_description="test")
    pydantic_warns = [w for w in recwarn.list if "model_hint" in str(w.message)]
    assert pydantic_warns == [], "model_hint triggers Pydantic protected-namespace warning"


def test_ultrathink_response_no_model_used_namespace_warning(recwarn):
    UltraThinkResponse(
        status="success",
        result="ok",
        model_used="some-model",
        execution_time_ms=1,
        reasoning_depth="standard",
        metadata={},
    )
    pydantic_warns = [w for w in recwarn.list if "model_used" in str(w.message)]
    assert pydantic_warns == [], "model_used triggers Pydantic protected-namespace warning"


# ── /ultrathink endpoint includes session_id and nodes_visited in JSON output ─

def test_http_endpoint_returns_session_id_and_nodes_visited(monkeypatch):
    """End-to-end: POST /ultrathink with session_id → response JSON has both fields."""
    from fastapi.testclient import TestClient

    async def fake_call(prompt, model, max_tokens, temperature):
        return "v2 output", "http://localhost:1234"

    monkeypatch.setattr(api_server, "_call_with_fallback", fake_call)

    client = TestClient(api_server.app)
    resp = client.post("/ultrathink", json={
        "task_description": "test v2 shape",
        "session_id": "sess-xyz",
    })
    assert resp.status_code == 200
    body = resp.json()
    assert body["session_id"] == "sess-xyz"
    assert "nodes_visited" in body
    assert isinstance(body["nodes_visited"], list)
    assert "retry_count" in body
    assert isinstance(body["retry_count"], int)


# ── qwen3.5-9b-mlx thinking-model response extraction contract ───────────────
# Documents the expected behavior for the future real LM Studio HTTP client.
# The stub _call_with_fallback is mocked here; the real implementation must
# extract `content` not `reasoning_content` from thinking model responses.

def _extract_content_from_lm_studio_response(response_json: dict) -> str:
    """Reference extractor: ignores reasoning_content, returns final content."""
    msg = response_json["choices"][0]["message"]
    return msg.get("content", "") or ""


def test_extract_content_ignores_reasoning_content():
    thinking_response = {
        "choices": [{
            "message": {
                "role": "assistant",
                "content": "\n\nOK",
                "reasoning_content": "Thinking Process:\n1. The user wants OK\n2. I reply OK",
            },
            "finish_reason": "stop",
        }]
    }
    assert _extract_content_from_lm_studio_response(thinking_response) == "\n\nOK"


def test_extract_content_returns_empty_on_truncated_thinking():
    """When max_tokens is too low, content is empty (thinking didn't finish)."""
    truncated_response = {
        "choices": [{
            "message": {
                "role": "assistant",
                "content": "",
                "reasoning_content": "Thinking Process:\n1. An",
            },
            "finish_reason": "length",
        }]
    }
    assert _extract_content_from_lm_studio_response(truncated_response) == ""


def test_extract_content_handles_non_thinking_model():
    """Standard (non-thinking) model: content is present, no reasoning_content."""
    standard_response = {
        "choices": [{
            "message": {
                "role": "assistant",
                "content": "Hello!",
            },
            "finish_reason": "stop",
        }]
    }
    assert _extract_content_from_lm_studio_response(standard_response) == "Hello!"
