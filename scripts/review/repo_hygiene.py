#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path


APPROVED_NAME = "cyre"
APPROVED_EMAIL = "Lawrence@cyre.me"
FORBIDDEN_TOKENS = (
    "Lawrence " + "Melgarejo",
    "Lawrence" + "@bettermind.ph",
)
PRIVATE_GENERATED_TRACKED = {".env", ".env.local", ".paths"}
WORKFLOW_WRITE_MARKERS = (
    "softprops/action-gh-release",
    "peter-evans/create-pull-request",
    "gh pr",
    "gh release",
    "git push",
)
LEGACY_NAME = "ultrathink-system"
HISTORICAL_HINTS = (
    "previous identity",
    "renamed",
    "historical",
    "archive",
    "migration",
    "provenance",
    "carried over",
)


def run_git(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(root), *args],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def tracked_files(root: Path) -> list[str]:
    proc = run_git(root, "ls-files")
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or "git ls-files failed")
    return [line for line in proc.stdout.splitlines() if line]


def is_binary(path: Path) -> bool:
    try:
        chunk = path.read_bytes()[:4096]
    except OSError:
        return True
    return b"\0" in chunk


def scan_forbidden_identity(root: Path, files: list[str]) -> list[str]:
    errors: list[str] = []
    for rel in files:
        path = root / rel
        if not path.is_file() or is_binary(path):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for token in FORBIDDEN_TOKENS:
            if token in text:
                errors.append(f"forbidden identity token in tracked file: {rel}")
                break
    return errors


def check_private_generated_tracking(files: list[str]) -> list[str]:
    return [
        f"private/generated config is tracked: {rel}"
        for rel in files
        if rel in PRIVATE_GENERATED_TRACKED
    ]


def check_identity(root: Path) -> list[str]:
    name = run_git(root, "config", "user.name").stdout.strip()
    email = run_git(root, "config", "user.email").stdout.strip()
    if os.getenv("GITHUB_ACTIONS") == "true" and not name and not email:
        return []
    if name != APPROVED_NAME or email != APPROVED_EMAIL:
        return [
            "git identity mismatch: "
            f"found {name or '<unset>'} <{email or '<unset>'}>; "
            f"expected {APPROVED_NAME} <{APPROVED_EMAIL}>"
        ]
    return []


def check_ecc(root: Path, files: list[str]) -> list[str]:
    if ".ecc" not in files:
        return []
    ecc_path = root / ".ecc"
    mode = run_git(root, "ls-files", "-s", ".ecc").stdout.strip().split()
    is_gitlink = bool(mode and mode[0] == "160000")
    if is_gitlink and not (root / ".gitmodules").exists():
        return [".ecc is tracked as a gitlink but .gitmodules is absent"]
    if is_gitlink and ecc_path.is_symlink():
        return [".ecc is a gitlink in index but a symlink in the working tree"]
    return []


def check_workflow_permissions(root: Path) -> list[str]:
    errors: list[str] = []
    workflow_dir = root / ".github" / "workflows"
    if not workflow_dir.exists():
        return errors
    for path in sorted(workflow_dir.glob("*.y*ml")):
        text = path.read_text(encoding="utf-8")
        needs_write = any(marker in text for marker in WORKFLOW_WRITE_MARKERS)
        if not needs_write:
            continue
        rel = path.relative_to(root)
        if "contents: write" not in text and "pull-requests: write" not in text:
            errors.append(f"workflow may write but lacks explicit write permission: {rel}")
    return errors


def classify_legacy_name_refs(root: Path, files: list[str]) -> tuple[int, int]:
    active = 0
    historical = 0
    for rel in files:
        path = root / rel
        if not path.is_file() or is_binary(path):
            continue
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except UnicodeDecodeError:
            continue
        for line in lines:
            if LEGACY_NAME not in line:
                continue
            lower = line.lower()
            if any(hint in lower for hint in HISTORICAL_HINTS) or "docs/recovery/" in rel:
                historical += 1
            else:
                active += 1
    return active, historical


def report_status(root: Path) -> list[str]:
    warnings: list[str] = []
    status = run_git(root, "status", "--short", "--branch")
    if status.returncode != 0:
        return [f"git status failed: {status.stderr.strip()}"]
    warnings.append(status.stdout.strip())

    shallow = run_git(root, "rev-parse", "--is-shallow-repository")
    if shallow.returncode == 0:
        warnings.append(f"shallow={shallow.stdout.strip()}")
    return warnings


def main() -> int:
    parser = argparse.ArgumentParser(description="Repo hygiene guard for orama-system salvage work")
    parser.add_argument("repo", nargs="?", default=".", help="repository root")
    args = parser.parse_args()

    root = Path(args.repo).resolve()
    files = tracked_files(root)

    errors: list[str] = []
    errors.extend(check_identity(root))
    errors.extend(scan_forbidden_identity(root, files))
    errors.extend(check_private_generated_tracking(files))
    errors.extend(check_ecc(root, files))
    errors.extend(check_workflow_permissions(root))
    active_legacy, historical_legacy = classify_legacy_name_refs(root, files)

    for line in report_status(root):
        print(f"INFO: {line}")
    print(
        "INFO: legacy name references "
        f"active={active_legacy} historical_or_allowed={historical_legacy}"
    )

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    print("OK: repo hygiene checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
