"""tests/test_bridge.py — OramaToPTBridge: verifier gate + parallel fan-out.

Tests the two hard invariants from unified-absorption-plan.md § 5.5:
  1. dispatch_crystallization() raises PermissionError when verdict != "approved".
  2. dispatch_parallel() fans out multiple workers concurrently and returns
     results in submission order.

These tests use asyncio and mock PT's supervisor to avoid needing a live PT env.
"""
from __future__ import annotations

import asyncio
import sys
import types
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_verification_result(verdict: str) -> Any:
    """Build a minimal duck-type VerificationResult."""
    obj = MagicMock()
    obj.verdict = verdict
    return obj


# ── Verifier gate tests ───────────────────────────────────────────────────────

class TestVerifierGate:
    """dispatch_crystallization() must enforce the verifier gate — always."""

    def _make_bridge(self):
        from bin.agents.dispatcher import OramaToPTBridge
        return OramaToPTBridge(
            session_id="sess-test",
            parent_orchestrator_id="orch-test",
        )

    @pytest.mark.asyncio
    async def test_approved_verdict_dispatches(self):
        """verdict='approved' allows crystallization to proceed."""
        bridge = self._make_bridge()
        vr = _make_verification_result("approved")

        async def _fake_dispatch_worker(**kwargs):
            return {"backend": "ollama", "output": "crystallized"}

        with patch.object(bridge, "dispatch_worker", side_effect=_fake_dispatch_worker):
            result = await bridge.dispatch_crystallization(
                prompt="Crystallize this",
                verification_result=vr,
            )
        assert result["output"] == "crystallized"

    @pytest.mark.asyncio
    async def test_needs_revision_blocks_crystallization(self):
        """verdict='needs_revision' must block crystallization with PermissionError."""
        bridge = self._make_bridge()
        vr = _make_verification_result("needs_revision")

        with pytest.raises(PermissionError, match="needs_revision"):
            await bridge.dispatch_crystallization(
                prompt="This should be blocked",
                verification_result=vr,
            )

    @pytest.mark.asyncio
    async def test_failed_verdict_blocks_crystallization(self):
        """verdict='failed' must block crystallization with PermissionError."""
        bridge = self._make_bridge()
        vr = _make_verification_result("failed")

        with pytest.raises(PermissionError, match="failed"):
            await bridge.dispatch_crystallization(
                prompt="Also blocked",
                verification_result=vr,
            )

    @pytest.mark.asyncio
    async def test_none_verdict_blocks_crystallization(self):
        """Missing verdict attribute must block crystallization."""
        bridge = self._make_bridge()
        # Object with no verdict attr at all → getattr returns None
        vr = MagicMock(spec=[])  # spec=[] means no attributes
        with pytest.raises(PermissionError):
            await bridge.dispatch_crystallization(
                prompt="Blocked by missing verdict",
                verification_result=vr,
            )

    @pytest.mark.asyncio
    async def test_error_message_contains_verdict(self):
        """PermissionError message must contain the actual bad verdict string."""
        bridge = self._make_bridge()
        vr = _make_verification_result("partially_approved")  # invalid value

        with pytest.raises(PermissionError) as exc_info:
            await bridge.dispatch_crystallization(
                prompt="Blocked",
                verification_result=vr,
            )
        assert "partially_approved" in str(exc_info.value)


# ── Parallel fan-out tests ─────────────────────────────────────────────────────

class TestParallelFanOut:
    """dispatch_parallel() must run workers concurrently and preserve order."""

    def _make_bridge(self):
        from bin.agents.dispatcher import OramaToPTBridge
        return OramaToPTBridge(
            session_id="sess-parallel",
            parent_orchestrator_id="orch-parallel",
        )

    @pytest.mark.asyncio
    async def test_parallel_results_in_submission_order(self):
        """Results must come back in the same order as the submitted workers list."""
        bridge = self._make_bridge()

        call_order = []

        async def _fake_worker(**kwargs):
            call_order.append(kwargs["role"])
            return {"role": kwargs["role"], "output": f"done:{kwargs['role']}"}

        workers = [
            {"role": "context-agent",     "intent": "research",   "prompt": "p1"},
            {"role": "architect-agent",   "intent": "design",     "prompt": "p2"},
            {"role": "executor-agent",    "intent": "write-code", "prompt": "p3"},
        ]

        with patch.object(bridge, "dispatch_worker", side_effect=_fake_worker):
            results = await bridge.dispatch_parallel(workers)

        assert len(results) == 3
        assert results[0]["output"] == "done:context-agent"
        assert results[1]["output"] == "done:architect-agent"
        assert results[2]["output"] == "done:executor-agent"

    @pytest.mark.asyncio
    async def test_parallel_empty_list_returns_empty(self):
        """Empty worker list returns empty results without error."""
        bridge = self._make_bridge()
        results = await bridge.dispatch_parallel([])
        assert results == []

    @pytest.mark.asyncio
    async def test_parallel_one_worker(self):
        """Single-element list behaves like a regular dispatch."""
        bridge = self._make_bridge()

        async def _fake_worker(**kwargs):
            return {"output": "single-result"}

        workers = [{"role": "verifier-agent", "intent": "verify", "prompt": "p"}]

        with patch.object(bridge, "dispatch_worker", side_effect=_fake_worker):
            results = await bridge.dispatch_parallel(workers)

        assert len(results) == 1
        assert results[0]["output"] == "single-result"

    @pytest.mark.asyncio
    async def test_parallel_propagates_worker_error(self):
        """If one worker raises, dispatch_parallel propagates the exception."""
        bridge = self._make_bridge()

        async def _failing(**kwargs):
            if kwargs["role"] == "executor-agent":
                raise RuntimeError("executor bombed")
            return {"output": "ok"}

        workers = [
            {"role": "context-agent",  "intent": "research",   "prompt": "p1"},
            {"role": "executor-agent", "intent": "write-code", "prompt": "p2"},
        ]

        with patch.object(bridge, "dispatch_worker", side_effect=_failing):
            with pytest.raises(RuntimeError, match="executor bombed"):
                await bridge.dispatch_parallel(workers)


# ── Gate-integration: crystallization only after verifier ─────────────────────

class TestGateIntegration:
    """Integration: simulated stage sequence enforcing the gate order."""

    @pytest.mark.asyncio
    async def test_stage_sequence_blocks_crystallize_before_verify(self):
        """A full sequence that skips verification must not reach crystallization."""
        from bin.agents.dispatcher import OramaToPTBridge

        bridge = OramaToPTBridge(
            session_id="sess-gate-integration",
            parent_orchestrator_id="orch-main",
        )

        # No verification step — must not crystallize
        unverified_result = MagicMock()
        unverified_result.verdict = "needs_revision"

        with pytest.raises(PermissionError):
            await bridge.dispatch_crystallization(
                prompt="premature crystallize",
                verification_result=unverified_result,
            )

    @pytest.mark.asyncio
    async def test_stage_sequence_allows_crystallize_after_approval(self):
        """Approved VerificationResult unlocks crystallization."""
        from bin.agents.dispatcher import OramaToPTBridge

        bridge = OramaToPTBridge(
            session_id="sess-gate-integration-ok",
            parent_orchestrator_id="orch-main",
        )

        approved = _make_verification_result("approved")

        async def _fake_worker(**kwargs):
            return {"backend": "ollama", "output": "final summary"}

        with patch.object(bridge, "dispatch_worker", side_effect=_fake_worker):
            result = await bridge.dispatch_crystallization(
                prompt="crystallize the approved output",
                verification_result=approved,
            )

        assert result["output"] == "final summary"
