#!/usr/bin/env python3
"""
test_single_agent.py
====================
Test suite for the ultrathink single-agent skill package.
Run: pytest tests/test_single_agent.py -v
"""
import os
import pytest
from pathlib import Path

ROOT = Path(__file__).parent.parent
SINGLE = ROOT / "single_agent"


class TestPackageIntegrity:
    def test_skill_md_exists(self):
        assert (SINGLE / "SKILL.md").exists(), "SKILL.md not found"

    def test_skill_md_has_frontmatter(self):
        content = (SINGLE / "SKILL.md").read_text()
        assert content.startswith("---"), "SKILL.md must start with YAML frontmatter"
        assert "name: ultrathink-system-skill" in content
        assert "version:" in content
        assert "license: Apache 2.0" in content

    def test_skill_md_under_500_lines(self):
        lines = (SINGLE / "SKILL.md").read_text().splitlines()
        assert len(lines) < 500, f"SKILL.md is {len(lines)} lines (max 500)"

    def test_skill_md_has_required_sections(self):
        content = (SINGLE / "SKILL.md").read_text()
        required = ["Execution Mode Router", "CIDF v1.2", "MODE 1",
                    "The 6 Directives", "Boundaries", "Success Criteria"]
        for section in required:
            assert section in content, f"Missing section: {section}"

    def test_references_exist(self):
        refs = SINGLE / "references"
        expected = ["ultrathink-5-stages.md", "core-operational-directives.md",
                    "content-insertion-framework.md", "skill-architecture-guide.md"]
        for f in expected:
            assert (refs / f).exists(), f"Missing reference: {f}"

    def test_scripts_exist(self):
        scripts = SINGLE / "scripts"
        expected = ["verify_before_done.py", "capture_lesson.py",
                    "create_task_plan.sh", "README.md"]
        for f in expected:
            assert (scripts / f).exists(), f"Missing script: {f}"

    def test_templates_exist(self):
        templates = SINGLE / "templates"
        expected = ["task-plan.md", "lessons-log.md", "verification-checklist.md"]
        for f in expected:
            assert (templates / f).exists(), f"Missing template: {f}"

    def test_scripts_are_executable(self):
        scripts_dir = SINGLE / "scripts"
        for script in scripts_dir.glob("*.py"):
            assert os.access(script, os.R_OK), f"{script.name} is not readable"
        for script in scripts_dir.glob("*.sh"):
            assert (scripts_dir / script.name).exists()


class TestContentQuality:
    def test_cidf_has_json_block(self):
        cidf = (SINGLE / "references" / "content-insertion-framework.md").read_text()
        assert "method_registry" in cidf, "CIDF missing method_registry JSON block"
        assert "automation_gate" in cidf, "CIDF missing automation_gate"

    def test_5stages_covers_all_stages(self):
        content = (SINGLE / "references" / "ultrathink-5-stages.md").read_text()
        for stage in ["Context Immersion", "Visionary Architecture",
                      "Ruthless Refinement", "Masterful Execution", "Crystallize"]:
            assert stage in content, f"5-stages doc missing: {stage}"

    def test_directives_covers_all_6(self):
        content = (SINGLE / "references" / "core-operational-directives.md").read_text()
        for directive in ["Plan Node", "Subagent", "Self-Improvement",
                          "Verification", "Elegance", "Autonomous Bug"]:
            assert directive in content, f"Directives doc missing: {directive}"

    def test_task_plan_template_has_checkboxes(self):
        content = (SINGLE / "templates" / "task-plan.md").read_text()
        assert "- [ ]" in content, "task-plan.md must have checkable items"

    def test_lessons_template_has_format(self):
        content = (SINGLE / "templates" / "lessons-log.md").read_text()
        assert "What Went Wrong" in content
        assert "Prevention Rule" in content
        assert "Root Cause" in content

    def test_verification_checklist_has_7_categories(self):
        content = (SINGLE / "templates" / "verification-checklist.md").read_text()
        categories = ["Unit Tests", "Integration Tests", "Manual Testing",
                      "Code Quality", "Diff Review", "Documentation", "Security"]
        for cat in categories:
            assert cat in content, f"Missing checklist category: {cat}"


class TestCIDF:
    """Verify the full CIDF runnable package is present and functional."""

    CIDF = Path(__file__).parent.parent / "single_agent" / "cidf"

    def test_cidf_directory_exists(self):
        assert self.CIDF.is_dir(), "single_agent/cidf/ not found"

    def test_core_python_exists(self):
        assert (self.CIDF / "core" / "content_insertion_framework.py").exists()

    def test_policy_json_exists(self):
        assert (self.CIDF / "core" / "content_insertion_policy.json").exists()

    def test_typescript_core_exists(self):
        assert (self.CIDF / "core" / "contentInsertionFramework.ts").exists()

    def test_linter_python_exists(self):
        assert (self.CIDF / "linter" / "policy_linter.py").exists()

    def test_linter_typescript_exists(self):
        assert (self.CIDF / "linter" / "policyLinter.ts").exists()

    def test_conformance_tests_exist(self):
        assert (self.CIDF / "tests" / "test_conformance.py").exists()
        assert (self.CIDF / "tests" / "conformance.test.ts").exists()

    def test_framework_doc_exists(self):
        assert (self.CIDF / "FRAMEWORK.md").exists()

    def test_readme_exists(self):
        assert (self.CIDF / "README.md").exists()

    def test_policy_json_is_valid(self):
        import json
        data = json.loads((self.CIDF / "core" / "content_insertion_policy.json").read_text())
        assert data["framework_version"] == "1.2"
        assert len(data["tool_priority_order"]) == 5
        assert len(data["test_vectors"]) == 6
        assert data["verification"]["must_verify"] is True

    def test_python_decide_function_importable(self):
        import sys
        sys.path.insert(0, str(self.CIDF.parent))
        from cidf.core.content_insertion_framework import decide, Task, Env
        task = Task(
            task_type="content_insertion", is_one_time=True, frequency_estimate=1,
            content_static=True, requires_transformation=False,
            requires_conditional_logic=False, requires_external_integration=False,
            content_length_chars=500, format_requirements="plain", signature="test"
        )
        env = Env(field_accessible=True, editor_visible=True, paste_supported=True, upload_available=False)
        d = decide(task, env)
        assert d.chosen_tool == "direct_form_input"
        assert d.verification_required is True

    def test_linter_catches_premature_scripting(self):
        import sys
        sys.path.insert(0, str(self.CIDF.parent))
        from cidf.core.content_insertion_framework import decide, Task, Env, Decision
        from cidf.linter.policy_linter import lint
        task = Task(
            task_type="content_insertion", is_one_time=True, frequency_estimate=1,
            content_static=True, requires_transformation=False,
            requires_conditional_logic=False, requires_external_integration=False,
            content_length_chars=500, format_requirements="plain", signature="test"
        )
        env = Env(field_accessible=True, editor_visible=True, paste_supported=True, upload_available=False)
        bad_decision = Decision(
            chosen_tool="scripting", fallback_chain=[],
            reason_codes=["forced"], automation_justified=False
        )
        violations = lint(bad_decision, task, env)
        rule_ids = [v.rule_id for v in violations]
        assert "LINT-001" in rule_ids
