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


def test_bridge_doc_references_live_mcp_tool_names():
    content = BRIDGE_DOC.read_text()

    for schema in TOOL_SCHEMAS:
        assert f"`{schema['name']}`" in content


def test_bridge_doc_marks_http_path_as_future_backup():
    content = BRIDGE_DOC.read_text()

    assert "future backup" in content
    assert "TODO" in content
    assert "not implemented in this repo checkout" in content
