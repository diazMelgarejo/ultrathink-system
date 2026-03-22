#!/usr/bin/env python3
"""
test_multi_agent.py
===================
Test suite for the ultrathink multi-agent package structure.
Run: pytest tests/test_multi_agent.py -v
"""
import json
import pytest
from pathlib import Path

ROOT   = Path(__file__).parent.parent
MULTI  = ROOT / "multi-agent"
AGENTS = ["orchestrator", "context", "architect", "refiner", "executor", "verifier", "crystallizer"]
SKILL_NAMES = {
    "orchestrator": "ultrathink-orchestrator.md",
    "context":      "context-immersion-agent.md",
    "architect":    "visionary-architect-agent.md",
    "refiner":      "ruthless-refiner-agent.md",
    "executor":     "masterful-executor-agent.md",
    "verifier":     "verification-agent.md",
    "crystallizer": "vision-crystallizer-agent.md",
}


class TestAgentStructure:
    @pytest.mark.parametrize("agent", AGENTS)
    def test_agent_directory_exists(self, agent):
        assert (MULTI / "agents" / agent).is_dir()

    @pytest.mark.parametrize("agent", AGENTS)
    def test_agent_skill_md_exists(self, agent):
        skill_file = SKILL_NAMES[agent]
        path = MULTI / "agents" / agent / skill_file
        assert path.exists(), f"Missing SKILL.md for {agent}: {skill_file}"

    @pytest.mark.parametrize("agent", AGENTS)
    def test_agent_skill_has_frontmatter(self, agent):
        skill_file = SKILL_NAMES[agent]
        content = (MULTI / "agents" / agent / skill_file).read_text()
        assert content.startswith("---"), f"{agent} SKILL.md must start with ---"
        assert "version:" in content
        assert "license: Apache 2.0" in content

    @pytest.mark.parametrize("agent", AGENTS)
    def test_agent_has_readme(self, agent):
        assert (MULTI / "agents" / agent / "README.md").exists()

    @pytest.mark.parametrize("agent", AGENTS)
    def test_agent_has_tools_py(self, agent):
        tools_map = {
            "orchestrator": "orchestrator_logic.py",
            "context":      "context_tools.py",
            "architect":    "architecture_tools.py",
            "refiner":      "refinement_tools.py",
            "executor":     "execution_tools.py",
            "verifier":     "verification_tools.py",
            "crystallizer": "documentation_tools.py",
        }
        assert (MULTI / "agents" / agent / tools_map[agent]).exists()


class TestSharedUtilities:
    def test_ultrathink_core_exists(self):
        assert (MULTI / "shared" / "ultrathink_core.py").exists()

    def test_state_manager_exists(self):
        assert (MULTI / "shared" / "state_manager.py").exists()

    def test_message_bus_exists(self):
        assert (MULTI / "shared" / "message_bus.py").exists()

    def test_core_has_stage_enum(self):
        content = (MULTI / "shared" / "ultrathink_core.py").read_text()
        assert "class Stage" in content
        assert "context_immersion" in content

    def test_core_has_task_state(self):
        content = (MULTI / "shared" / "ultrathink_core.py").read_text()
        assert "class TaskState" in content
        assert "elegance_score" in content


class TestConfig:
    def test_agent_registry_valid_json(self):
        path = MULTI / "config" / "agent_registry.json"
        assert path.exists()
        data = json.loads(path.read_text())
        assert "agents" in data
        assert len(data["agents"]) == 7

    def test_all_agents_in_registry(self):
        data = json.loads((MULTI / "config" / "agent_registry.json").read_text())
        ids = [a["id"] for a in data["agents"]]
        for agent in ["orchestrator", "context-agent", "architect-agent",
                      "refiner-agent", "executor-agent", "verifier-agent", "crystallizer-agent"]:
            assert agent in ids, f"{agent} missing from registry"

    def test_routing_rules_valid_json(self):
        path = MULTI / "config" / "routing_rules.json"
        assert path.exists()
        data = json.loads(path.read_text())
        assert "rules" in data
        assert len(data["rules"]) > 5

    def test_mcp_servers_exist(self):
        assert (MULTI / "mcp_servers" / "ultrathink_orchestration_server.py").exists()
        assert (MULTI / "mcp_servers" / "agent_communication_server.py").exists()
