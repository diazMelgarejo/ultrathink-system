#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


def check_openclaw(config_path: Path) -> int:
    if not config_path.exists():
        print(f"[policy] openclaw config not found: {config_path}")
        return 0
    try:
        data = json.loads(config_path.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"[policy] invalid json in {config_path}: {exc}")
        return 1
    providers = (data.get("models") or {}).get("providers") or {}
    print(f"[policy] providers discovered: {', '.join(sorted(providers.keys())) or '(none)'}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Hardware policy helper checks")
    parser.add_argument("--check-openclaw", action="store_true", help="validate ~/.openclaw/openclaw.json shape")
    args = parser.parse_args()
    if args.check_openclaw:
        return check_openclaw(Path.home() / ".openclaw" / "openclaw.json")
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

