#!/usr/bin/env python3
from __future__ import annotations

import argparse
import fnmatch
import os
import re
import subprocess
import sys
from pathlib import Path


APPROVED_NAME = "cyre"
APPROVED_EMAIL = "Lawrence@cyre.me"
FORBIDDEN_TOKENS = (
    "Lawrence " + "Melgarejo",
    "Lawrence" + "@bettermind.ph",
)
IDENTITY_DOC_EXCEPTIONS = {
    ".mailmap",
    "docs/wiki/08-git-hygiene-and-branching.md",
}
PRIVATE_GENERATED_TRACKED = {".env", ".env.local", ".paths"}
MARKDOWN_LINK_PATTERN = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
NEW_MARKDOWN_LINE_WARN = 200
EXISTING_MARKDOWN_LINE_WARN = 500
GENERATED_ARTIFACT_PATTERNS = (
    ".DS_Store",
    "*/.DS_Store",
    "._*",
    "*/._*",
    "__pycache__/*",
    "*/__pycache__/*",
    "*.pyc",
    "*.pyo",
    ".pytest_cache/*",
    "*/.pytest_cache/*",
    ".mypy_cache/*",
    "*/.mypy_cache/*",
    "dist/*",
    "*/dist/*",
    "build/*",
    "*/build/*",
    "DerivedData/*",
    "*/DerivedData/*",
    "*.egg-info/*",
    "*.whl",
    "*.tar.gz",
    "*.xcuserstate",
    "*.xcscmblueprint",
    "*.xcodeproj/xcuserdata/*",
    "*.xcworkspace/xcuserdata/*",
    "*.xcuserdatad/*",
)
WORKFLOW_WRITE_MARKERS = (
    "softprops/action-gh-release",
    "peter-evans/create-pull-request",
    "gh pr",
    "gh release",
    "git push",
)
LEGACY_NAME = "ultrathink-system"
STALE_SKILL_REF_TOKENS = (
    "bin/" + "skills",
    "bin" + ".skills",
)
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
        if rel in IDENTITY_DOC_EXCEPTIONS:
            continue
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


def check_markdown_link_hygiene(root: Path, files: list[str]) -> list[str]:
    errors: list[str] = []
    for rel in files:
        if not rel.endswith(".md"):
            continue
        path = root / rel
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for target in MARKDOWN_LINK_PATTERN.findall(text):
            normalized = target.strip()
            if normalized.startswith("<") and normalized.endswith(">"):
                normalized = normalized[1:-1].strip()
            if normalized.startswith(("http://", "https://", "#", "mailto:")):
                continue
            if normalized.startswith("file://") or normalized.startswith("/") or re.match(r"^[A-Za-z]:[\\/]", normalized):
                errors.append(f"markdown link must be repo-relative: {rel} -> {normalized}")
    return errors


def changed_markdown_files(root: Path) -> set[str]:
    changed: set[str] = set()
    for args in (
        ("diff", "--name-only", "--diff-filter=ACMR", "HEAD", "--", "*.md"),
        ("diff", "--cached", "--name-only", "--diff-filter=ACMR", "HEAD", "--", "*.md"),
    ):
        proc = run_git(root, *args)
        if proc.returncode == 0:
            changed.update(line for line in proc.stdout.splitlines() if line.endswith(".md"))
    return changed


def exists_in_head(root: Path, rel: str) -> bool:
    proc = run_git(root, "cat-file", "-e", f"HEAD:{rel}")
    return proc.returncode == 0


def check_markdown_size_warnings(
    root: Path,
    files: list[str],
    changed: set[str] | None = None,
    existing: set[str] | None = None,
) -> list[str]:
    warnings: list[str] = []
    changed = changed_markdown_files(root) if changed is None else changed
    for rel in sorted(changed):
        if rel not in files or not rel.endswith(".md"):
            continue
        path = root / rel
        if not path.is_file():
            continue
        try:
            line_count = len(path.read_text(encoding="utf-8").splitlines())
        except UnicodeDecodeError:
            continue
        existed_before = rel in existing if existing is not None else exists_in_head(root, rel)
        if not existed_before and line_count > NEW_MARKDOWN_LINE_WARN:
            warnings.append(
                f"{rel} has {line_count} lines; new markdown files over "
                f"{NEW_MARKDOWN_LINE_WARN} lines should ask the user about offloading "
                "related content to references/ or sub-skills"
            )
        if existed_before and line_count > EXISTING_MARKDOWN_LINE_WARN:
            warnings.append(
                f"{rel} has {line_count} lines; existing markdown files over "
                f"{EXISTING_MARKDOWN_LINE_WARN} lines should ask the user about splitting "
                "or redirecting detailed content elsewhere"
            )
    return warnings


def check_generated_artifact_tracking(files: list[str]) -> list[str]:
    errors: list[str] = []
    for rel in files:
        if any(fnmatch.fnmatch(rel, pattern) for pattern in GENERATED_ARTIFACT_PATTERNS):
            errors.append(f"generated artifact is tracked: {rel}")
    return errors


def check_git_internal_junk(root: Path) -> list[str]:
    git_dir = root / ".git"
    refs_dir = git_dir / "refs"
    if not refs_dir.exists():
        return []
    return [
        f"macOS metadata file inside git refs: {path.relative_to(root)}"
        for path in refs_dir.rglob(".DS_Store")
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


def check_stale_skill_path_refs(root: Path, files: list[str]) -> list[str]:
    errors: list[str] = []
    for rel in files:
        path = root / rel
        if not path.is_file() or is_binary(path):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for token in STALE_SKILL_REF_TOKENS:
            if token in text:
                errors.append(f"stale skill path/module reference in tracked file: {rel} -> {token}")
                break
    return errors


def classify_legacy_name_refs(root: Path, files: list[str]) -> tuple[int, int]:
    active = 0
    historical = 0
    for rel in files:
        if rel == "scripts/review/repo_hygiene.py":
            continue
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
    errors.extend(check_markdown_link_hygiene(root, files))
    errors.extend(check_generated_artifact_tracking(files))
    errors.extend(check_ecc(root, files))
    errors.extend(check_workflow_permissions(root))
    errors.extend(check_stale_skill_path_refs(root, files))
    errors.extend(check_git_internal_junk(root))
    warnings = check_markdown_size_warnings(root, files)
    active_legacy, historical_legacy = classify_legacy_name_refs(root, files)

    for line in report_status(root):
        print(f"INFO: {line}")
    print(
        "INFO: legacy name references "
        f"active={active_legacy} historical_or_allowed={historical_legacy}"
    )
    for warning in warnings:
        print(f"WARNING: {warning}")

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    print("OK: repo hygiene checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
