from __future__ import annotations

import subprocess
from pathlib import Path


ROOT = Path(__file__).parent.parent


def test_private_generated_config_is_not_tracked():
    tracked = subprocess.check_output(
        ["git", "-C", str(ROOT), "ls-files"],
        text=True,
    ).splitlines()

    assert ".env" not in tracked
    assert ".env.local" not in tracked
    assert ".paths" not in tracked


def test_repo_hygiene_script_runs_clean():
    result = subprocess.run(
        ["python", "scripts/review/repo_hygiene.py", "."],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    assert result.returncode == 0, result.stdout + result.stderr


def test_identity_check_script_is_shell_valid():
    subprocess.check_call(["bash", "-n", "scripts/git/check_identity.sh"], cwd=ROOT)
