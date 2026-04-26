"""test_agent_registry_schema.py — agent_registry.json schema consistency tests.

Verifies:
1. All entries in agents[], openclaw_agents{}, autoresearch_agents{} use 'affinity' key (not 'device_affinity').
2. All affinity values are non-empty strings.
3. No entry uses the deprecated 'device_affinity' key.
"""
from __future__ import annotations
import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent.parent
REGISTRY_PATH = REPO_ROOT / "bin" / "config" / "agent_registry.json"


@pytest.fixture(scope="module")
def registry() -> dict:
    return json.loads(REGISTRY_PATH.read_text())


def test_registry_file_exists():
    assert REGISTRY_PATH.exists(), f"Missing: {REGISTRY_PATH}"
    assert REGISTRY_PATH.stat().st_size > 0


def test_agents_array_use_affinity_key(registry):
    """All entries in agents[] must use 'affinity', not 'device_affinity'."""
    agents = registry.get("agents", [])
    assert len(agents) > 0, "agents[] must be non-empty"
    for agent in agents:
        agent_id = agent.get("id", "?")
        assert "device_affinity" not in agent, (
            f"agents[id={agent_id}] still uses deprecated 'device_affinity' key"
        )
        assert "affinity" in agent, (
            f"agents[id={agent_id}] is missing required 'affinity' key"
        )
        assert isinstance(agent["affinity"], str) and agent["affinity"], (
            f"agents[id={agent_id}] affinity must be a non-empty string"
        )


def test_openclaw_agents_use_affinity_key(registry):
    """All entries in openclaw_agents{} must use 'affinity'."""
    openclaw = registry.get("openclaw_agents", {})
    for name, agent in openclaw.items():
        if isinstance(agent, dict):
            assert "device_affinity" not in agent, (
                f"openclaw_agents[{name}] still uses deprecated 'device_affinity' key"
            )
            assert "affinity" in agent, (
                f"openclaw_agents[{name}] is missing required 'affinity' key"
            )


def test_autoresearch_agents_use_affinity_key(registry):
    """All entries in autoresearch_agents{} must use 'affinity', not 'device_affinity'."""
    autoresearch = registry.get("autoresearch_agents", {})
    for name, agent in autoresearch.items():
        if not isinstance(agent, dict) or name.startswith("_"):
            continue  # skip _comment entries
        assert "device_affinity" not in agent, (
            f"autoresearch_agents[{name}] still uses deprecated 'device_affinity' key — "
            "migrate to 'affinity'"
        )
        assert "affinity" in agent, (
            f"autoresearch_agents[{name}] is missing required 'affinity' key"
        )
        assert isinstance(agent["affinity"], str) and agent["affinity"], (
            f"autoresearch_agents[{name}] affinity must be a non-empty string"
        )


def test_no_device_affinity_anywhere_in_registry(registry):
    """Global scan: 'device_affinity' must not appear anywhere in the registry JSON."""
    raw = REGISTRY_PATH.read_text()
    assert "device_affinity" not in raw, (
        "Found deprecated 'device_affinity' key in agent_registry.json. "
        "Rename all occurrences to 'affinity'."
    )


def test_autoresearch_coder_targets_win_rtx3080(registry):
    """autoresearch-coder must target win-rtx3080 (specific device, not generic 'win')."""
    coder = registry["autoresearch_agents"].get("autoresearch-coder", {})
    assert coder.get("affinity") == "win-rtx3080", (
        f"autoresearch-coder affinity should be 'win-rtx3080', got {coder.get('affinity')!r}. "
        "Future Windows profiles will share the blocklist but have distinct whitelists."
    )


def test_mac_agents_target_mac(registry):
    """autoresearch-evaluator and autoresearch-orchestrator must target mac."""
    for name in ("autoresearch-evaluator", "autoresearch-orchestrator"):
        agent = registry["autoresearch_agents"].get(name, {})
        assert agent.get("affinity") == "mac", (
            f"{name} affinity should be 'mac', got {agent.get('affinity')!r}"
        )
