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
