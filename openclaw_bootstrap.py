#!/usr/bin/env python3
"""
openclaw_bootstrap.py - ultrathink-system delegate-only OpenClaw config applier
-----------------------------------------------------------------------------
Perplexity-Tools is the sole runtime authority. This script only:
  1. Reads the PT-resolved runtime payload
  2. Writes ~/.openclaw/openclaw.json using that exact payload
  3. Ensures local agent workspaces and SOUL.md files exist

Usage:
    python openclaw_bootstrap.py --apply
    python openclaw_bootstrap.py --apply --payload /path/to/runtime_payload.json
    python openclaw_bootstrap.py --apply --force
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_PAYLOAD = Path(".state/pt_runtime_payload.json")


def _payload_path(explicit: str | None = None) -> Path:
    if explicit:
        return Path(explicit)
    env_path = Path(sys.argv[0]).parent / ".state" / "pt_runtime_payload.json"
    return Path(
        os.environ.get("PT_RUNTIME_STATE")
        or os.environ.get("PT_RUNTIME_PAYLOAD")
        or env_path
    )


def load_runtime_payload(payload: str | None = None) -> dict[str, Any]:
    path = _payload_path(payload)
    if not path.exists():
        raise FileNotFoundError(
            f"PT runtime payload not found: {path}. "
            "Run Perplexity-Tools orchestrator.py bootstrap first."
        )
    return json.loads(path.read_text(encoding="utf-8"))


def _ensure_agent_workspaces(config_dir: Path) -> None:
    agents_dir = config_dir / "agents"
    roles = ["mac-researcher", "win-researcher", "orchestrator", "coder", "autoresearcher"]
    for role in roles:
        role_dir = agents_dir / role
        role_dir.mkdir(parents=True, exist_ok=True)
        soul_file = role_dir / "SOUL.md"
        if soul_file.exists():
            continue
        source = SCRIPT_DIR / "bin" / "agents" / role / "SOUL.md"
        if source.exists():
            shutil.copy(source, soul_file)
            print(f"[openclaw] wrote workspace for {role}")


def apply_runtime_payload(payload: dict[str, Any], force: bool = False) -> dict[str, Any]:
    openclaw_config = payload.get("gateway", {}).get("openclaw_config")
    if not openclaw_config:
        raise ValueError("PT runtime payload does not contain gateway.openclaw_config")

    config_dir = Path.home() / ".openclaw"
    config_file = config_dir / "openclaw.json"
    config_dir.mkdir(parents=True, exist_ok=True)

    if force or not config_file.exists() or json.loads(config_file.read_text(encoding="utf-8")) != openclaw_config:
        config_file.write_text(json.dumps(openclaw_config, indent=2), encoding="utf-8")
        print(f"[openclaw] applied PT-resolved config -> {config_file}")
    else:
        print(f"[openclaw] config already matches PT payload -> {config_file}")

    _ensure_agent_workspaces(config_dir)
    return {
        "applied": True,
        "config_path": str(config_file),
        "gateway_ready": bool(payload.get("gateway", {}).get("gateway_ready")),
        "gateway_url": payload.get("gateway", {}).get("gateway_url"),
        "topology": payload.get("role_routing", {}).get("topology"),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Delegate-only OpenClaw config applier for ultrathink-system",
    )
    parser.add_argument("--apply", action="store_true", help="Apply PT-resolved OpenClaw config")
    parser.add_argument("--payload", default=None, help="Path to PT runtime payload JSON")
    parser.add_argument("--force", action="store_true", help="Force-write openclaw.json")
    parser.add_argument("--json", action="store_true", help="Print the result as JSON")
    args = parser.parse_args()

    if not args.apply:
        parser.print_help()
        raise SystemExit(1)

    result = apply_runtime_payload(load_runtime_payload(args.payload), force=args.force)
    if args.json:
        print(json.dumps(result, indent=2))
    raise SystemExit(0)
