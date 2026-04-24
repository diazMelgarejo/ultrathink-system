from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).parent.parent
HYGIENE_PATH = ROOT / "scripts" / "review" / "repo_hygiene.py"


def load_repo_hygiene():
    spec = importlib.util.spec_from_file_location("repo_hygiene", HYGIENE_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_private_generated_config_is_not_tracked():
    tracked = subprocess.check_output(
        ["git", "-C", str(ROOT), "ls-files"],
        text=True,
    ).splitlines()

    assert ".env" not in tracked
    assert ".env.local" not in tracked
    assert ".paths" not in tracked


def test_generated_artifact_patterns_are_blocked():
    repo_hygiene = load_repo_hygiene()
    errors = repo_hygiene.check_generated_artifact_tracking(
        [
            ".DS_Store",
            "bin/shared/__pycache__/state_manager.cpython-312.pyc",
            "dist/orama_system-0.9.9.8.whl",
            "DerivedData/Build/Intermediates.noindex/file",
            "Project.xcodeproj/xcuserdata/user.xcuserdatad/UserInterfaceState.xcuserstate",
            "README.md",
        ]
    )

    assert errors == [
        "generated artifact is tracked: .DS_Store",
        "generated artifact is tracked: bin/shared/__pycache__/state_manager.cpython-312.pyc",
        "generated artifact is tracked: dist/orama_system-0.9.9.8.whl",
        "generated artifact is tracked: DerivedData/Build/Intermediates.noindex/file",
        "generated artifact is tracked: Project.xcodeproj/xcuserdata/user.xcuserdatad/UserInterfaceState.xcuserstate",
    ]


def test_git_internal_junk_is_blocked(tmp_path):
    repo_hygiene = load_repo_hygiene()
    refs_dir = tmp_path / ".git" / "refs" / "heads"
    refs_dir.mkdir(parents=True)
    (refs_dir / ".DS_Store").write_text("", encoding="utf-8")

    assert repo_hygiene.check_git_internal_junk(tmp_path) == [
        "macOS metadata file inside git refs: .git/refs/heads/.DS_Store"
    ]


def test_markdown_link_hygiene_blocks_absolute_paths(tmp_path):
    repo_hygiene = load_repo_hygiene()
    docs = tmp_path / "docs"
    docs.mkdir()
    md = docs / "README.md"
    md.write_text(
        "\n".join(
            [
                "[relative](wiki/README.md)",
                "[github](https://github.com/example/repo/blob/main/docs/README.md)",
                "[absolute](</Users/example/repo/docs/wiki/README.md>)",
            ]
        ),
        encoding="utf-8",
    )

    errors = repo_hygiene.check_markdown_link_hygiene(tmp_path, ["docs/README.md"])

    assert errors == [
        "markdown link must be repo-relative: docs/README.md -> /Users/example/repo/docs/wiki/README.md"
    ]


def test_markdown_size_warnings_for_changed_files(tmp_path):
    repo_hygiene = load_repo_hygiene()
    docs = tmp_path / "docs"
    docs.mkdir()
    new_doc = docs / "new-guide.md"
    old_doc = docs / "old-guide.md"
    small_doc = docs / "small-guide.md"
    new_doc.write_text("\n".join(["line"] * 201), encoding="utf-8")
    old_doc.write_text("\n".join(["line"] * 501), encoding="utf-8")
    small_doc.write_text("short\n", encoding="utf-8")

    warnings = repo_hygiene.check_markdown_size_warnings(
        tmp_path,
        ["docs/new-guide.md", "docs/old-guide.md", "docs/small-guide.md"],
        changed={"docs/new-guide.md", "docs/old-guide.md", "docs/small-guide.md"},
        existing={"docs/old-guide.md", "docs/small-guide.md"},
    )

    assert warnings == [
        "docs/new-guide.md has 201 lines; new markdown files over 200 lines should ask the user about offloading related content to references/ or sub-skills",
        "docs/old-guide.md has 501 lines; existing markdown files over 500 lines should ask the user about splitting or redirecting detailed content elsewhere",
    ]


def test_stale_skill_path_refs_are_blocked_in_hidden_tracked_files(tmp_path):
    repo_hygiene = load_repo_hygiene()
    workflow_dir = tmp_path / ".github" / "workflows"
    workflow_dir.mkdir(parents=True)
    workflow = workflow_dir / "ci.yml"
    stale_path = "bin/" + "skills"
    stale_module = "bin" + ".skills"
    workflow.write_text(f"grep -q Quick Start {stale_path}/SKILL.md\n", encoding="utf-8")
    package_check = tmp_path / "test-package-install.py"
    package_check.write_text(f"from {stale_module}.cidf.core import x\n", encoding="utf-8")

    errors = repo_hygiene.check_stale_skill_path_refs(
        tmp_path,
        [".github/workflows/ci.yml", "test-package-install.py"],
    )

    assert errors == [
        f"stale skill path/module reference in tracked file: .github/workflows/ci.yml -> {stale_path}",
        f"stale skill path/module reference in tracked file: test-package-install.py -> {stale_module}",
    ]


def test_repo_hygiene_script_runs_clean():
    result = subprocess.run(
        [sys.executable, "scripts/review/repo_hygiene.py", "."],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    assert result.returncode == 0, result.stdout + result.stderr


def test_identity_check_script_is_shell_valid():
    subprocess.check_call(["bash", "-n", "scripts/git/check_identity.sh"], cwd=ROOT)
