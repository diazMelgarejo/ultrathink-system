#!/usr/bin/env python3
"""
refresh_policy_cache.py — Sync orama's local hardware policy cache from PT.

The disaster recovery (DR) chain in api_server.py is:
  L1: Live import from PT (authoritative)
  L2: config/hardware_policy_cache.yml (this file — offline fallback)
  L3: Hard fail — never silently skip enforcement

This script refreshes L2 from PT's current config/model_hardware_policy.yml.
Run:
  - Manually:  python scripts/refresh_policy_cache.py
  - From cron: every 5 minutes (matching the openclaw.json check cadence)
  - From start.sh: on every stack startup

Usage:
    python scripts/refresh_policy_cache.py [--quiet] [--force]
    python scripts/refresh_policy_cache.py --status  # show cache age + hash

Exit codes:
    0 — cache refreshed (or already current)
    1 — PT not reachable, cache unchanged (no error — L2 still valid)
    2 — config error
"""

from __future__ import annotations

import argparse
import hashlib
import os
import shutil
import sys
import time
from pathlib import Path
from datetime import datetime, timezone

# ── Paths ─────────────────────────────────────────────────────────────────────

REPO_ROOT = Path(__file__).resolve().parents[1]
CACHE_FILE = REPO_ROOT / "config" / "hardware_policy_cache.yml"
LAST_REFRESH_STAMP = REPO_ROOT / "config" / ".policy_cache_refreshed"

PERPETUA_TOOLS_ROOT = Path(
    os.getenv(
        "PERPETUA_TOOLS_ROOT",
        REPO_ROOT.parent / "perplexity-api" / "Perpetua-Tools",
    )
)
PT_POLICY_SOURCE = PERPETUA_TOOLS_ROOT / "config" / "model_hardware_policy.yml"

# ── Helpers ───────────────────────────────────────────────────────────────────

def _sha256(path: Path) -> str:
    h = hashlib.sha256(path.read_bytes()).hexdigest()[:12]
    return h


def _age_seconds(path: Path) -> float:
    return time.time() - path.stat().st_mtime


def _stamp_header(source_path: Path) -> str:
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    sha = _sha256(source_path)
    return (
        f"# hardware_policy_cache.yml — orama-system offline DR fallback\n"
        f"# Source:  {source_path}\n"
        f"# Refreshed: {ts}  sha256:{sha}\n"
        f"#\n"
        f"# This file is the Layer-2 disaster recovery fallback.\n"
        f"# api_server.py uses it ONLY when PT is unreachable at startup.\n"
        f"# Refresh: python scripts/refresh_policy_cache.py\n"
        f"# DO NOT edit manually — it will be overwritten on next refresh.\n"
    )


# ── Core ──────────────────────────────────────────────────────────────────────

def refresh(force: bool = False, quiet: bool = False) -> int:
    def _log(msg: str):
        if not quiet:
            print(f"[refresh_policy_cache] {msg}")

    if not PT_POLICY_SOURCE.exists():
        _log(f"✗ PT policy source not found: {PT_POLICY_SOURCE}")
        _log("  Is PERPETUA_TOOLS_ROOT set correctly?")
        return 1

    # Check if already current (skip unless force)
    if not force and CACHE_FILE.exists():
        src_sha = _sha256(PT_POLICY_SOURCE)
        # Strip our header lines to get the content hash
        cache_lines = CACHE_FILE.read_text().splitlines()
        body_lines = [l for l in cache_lines if not l.startswith("#")]
        body_sha = hashlib.sha256("\n".join(body_lines).encode()).hexdigest()[:12]
        src_lines = [l for l in PT_POLICY_SOURCE.read_text().splitlines() if not l.startswith("#")]
        src_body_sha = hashlib.sha256("\n".join(src_lines).encode()).hexdigest()[:12]
        if body_sha == src_body_sha:
            age = _age_seconds(CACHE_FILE)
            _log(f"✓ Cache already current (sha:{src_sha}, age:{age:.0f}s)")
            return 0

    _log(f"Refreshing cache from {PT_POLICY_SOURCE} …")
    source_text = PT_POLICY_SOURCE.read_text()

    # Strip any existing header from source (it may have its own comments)
    # then prepend our DR header
    body_lines = [l for l in source_text.splitlines() if not l.startswith("#")]
    new_content = _stamp_header(PT_POLICY_SOURCE) + "\n".join(body_lines) + "\n"

    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    CACHE_FILE.write_text(new_content)
    LAST_REFRESH_STAMP.write_text(datetime.now(timezone.utc).isoformat())
    _log(f"✓ Cache refreshed → {CACHE_FILE}")
    return 0


def status():
    print(f"\n  Policy Cache Status")
    print(f"  {'─' * 46}")
    if CACHE_FILE.exists():
        age = _age_seconds(CACHE_FILE)
        sha = _sha256(CACHE_FILE)
        ts = datetime.fromtimestamp(CACHE_FILE.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
        print(f"  Cache file : {CACHE_FILE}")
        print(f"  Last write : {ts}  (age: {age:.0f}s)")
        print(f"  SHA-256    : {sha}")
    else:
        print(f"  Cache file : NOT FOUND — {CACHE_FILE}")
        print(f"  Run: python scripts/refresh_policy_cache.py to create it.")

    if PT_POLICY_SOURCE.exists():
        sha = _sha256(PT_POLICY_SOURCE)
        print(f"  PT source  : {PT_POLICY_SOURCE}  sha:{sha}")
    else:
        print(f"  PT source  : NOT FOUND — {PT_POLICY_SOURCE}")
        print(f"  Is PERPETUA_TOOLS_ROOT={PERPETUA_TOOLS_ROOT} correct?")
    print()


# ── Entry ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Refresh orama's local hardware policy cache from PT.")
    parser.add_argument("--quiet", "-q", action="store_true", help="Suppress output")
    parser.add_argument("--force", "-f", action="store_true", help="Refresh even if already current")
    parser.add_argument("--status", "-s", action="store_true", help="Show cache status and exit")
    args = parser.parse_args()
    if args.status:
        status()
        return
    sys.exit(refresh(force=args.force, quiet=args.quiet))


if __name__ == "__main__":
    main()
