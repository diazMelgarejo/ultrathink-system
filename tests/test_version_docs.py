from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).parent.parent


def test_active_version_surfaces_are_09994():
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    claude = (ROOT / "CLAUDE.md").read_text(encoding="utf-8")
    skill = (ROOT / "bin" / "skills" / "SKILL.md").read_text(encoding="utf-8")

    assert 'version = "0.9.9.4"' in pyproject
    assert "v0.9.9.4" in claude
    assert "version: 0.9.9.4" in skill


def test_readme_mentions_active_lan_helpers():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")

    assert "portal_server.py" in readme
    assert "network_autoconfig.py" in readme


def test_bridge_docs_reference_09994_and_bin_skills():
    bridge = (ROOT / "docs" / "PERPLEXITY_BRIDGE.md").read_text(encoding="utf-8")
    sync = (ROOT / "docs" / "SYNC_ANALYSIS.md").read_text(encoding="utf-8")

    assert "Version 0.9.9.4" in bridge
    assert "v0.9.9.4" in sync
