#!/usr/bin/env python3
"""
test_bridge_docs.py
===================
Regression tests for the MCP-first Perplexity bridge documentation.
"""
from __future__ import annotations

from pathlib import Path

from multi_agent.mcp_servers.ultrathink_orchestration_server import TOOL_SCHEMAS


ROOT = Path(__file__).parent.parent
BRIDGE_DOC = ROOT / "docs" / "PERPLEXITY_BRIDGE.md"
SYNC_ANALYSIS_DOC = ROOT / "docs" / "SYNC_ANALYSIS.md"
AFRP_SKILL = ROOT / "single_agent" / "afrp" / "SKILL.md"
AFRP_README = ROOT / "single_agent" / "afrp" / "README.md"
SINGLE_AGENT_SKILL = ROOT / "single_agent" / "SKILL.md"


def test_bridge_doc_references_live_mcp_tool_names():
    content = BRIDGE_DOC.read_text()

    for schema in TOOL_SCHEMAS:
        assert f"`{schema['name']}`" in content


def test_bridge_doc_marks_http_path_as_implemented_backup():
    content = BRIDGE_DOC.read_text()

    assert "backup compatibility bridge" in content
    assert "implemented in this repo checkout" in content
    assert "not the current primary contract" in content


def test_legacy_http_docs_are_marked_as_backup_or_historical():
    docs = {
        SYNC_ANALYSIS_DOC: "Historical analysis note:",
        AFRP_SKILL: "implemented backup HTTP `/ultrathink` path",
        AFRP_README: "implemented backup HTTP `/ultrathink` path",
        SINGLE_AGENT_SKILL: "backup HTTP `/ultrathink` is implemented via `api_server.py`",
    }

    for path, expected_text in docs.items():
        assert expected_text in path.read_text(), f"Missing backup marker in {path.name}"
