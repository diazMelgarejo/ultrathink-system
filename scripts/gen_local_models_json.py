#!/usr/bin/env python3
"""
gen_local_models_json.py — regenerate ~/.codex/local_models.json from live Ollama.

Usage:
    python3 scripts/gen_local_models_json.py > ~/.codex/local_models.json
    # or, to update in place:
    python3 scripts/gen_local_models_json.py --write

Requires Ollama running at http://localhost:11434.

See docs/v2/13-local-model-catalog-strategy.md for design context.
"""
import argparse
import json
import sys
import urllib.request
from datetime import date
from pathlib import Path

# Per-family safe local context caps (tokens).
# Raise a cap only after confirming the machine can handle it without OOM.
SAFE_CONTEXT_CAP: dict[str, int] = {
    "qwen3_5":    32768,
    "qwen2":      32768,
    "qwen3":      65536,   # larger families can handle more
    "nomic-bert":  2048,
}
DEFAULT_CAP = 32768

# Cloud-proxy model suffixes — served through Ollama but run remotely.
CLOUD_SUFFIXES = (":cloud",)

# Model families / name fragments that are embedding / reranker-only.
EMBED_FRAGMENTS = ("embed", "rerank", "nomic-bert")


def _get(url: str) -> dict:
    with urllib.request.urlopen(url, timeout=10) as resp:  # noqa: S310
        return json.loads(resp.read())


def _post(url: str, payload: dict) -> dict:
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        url, data=data, method="POST",
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=10) as resp:  # noqa: S310
        return json.loads(resp.read())


def get_tags(base: str) -> list[dict]:
    return _get(f"{base}/api/tags")["models"]


def get_model_info(base: str, name: str) -> dict:
    return _post(f"{base}/api/show", {"name": name})


def is_cloud(name: str) -> bool:
    return any(name.endswith(s) for s in CLOUD_SUFFIXES)


def is_non_generative(family: str, name: str) -> bool:
    combined = (family + " " + name).lower()
    return any(frag in combined for frag in EMBED_FRAGMENTS)


def build_entry(name: str, info: dict) -> dict:
    details = info.get("details", {})
    model_info = info.get("model_info", {})
    family: str = details.get("family", "")

    # Resolve native context length from Ollama model_info keys.
    native_ctx: int | None = None
    for k, v in model_info.items():
        if "context_length" in k:
            native_ctx = int(v)
            break

    cloud = is_cloud(name)
    non_gen = is_non_generative(family, name)

    if cloud:
        context_window = 131072
        max_output = 32768
    else:
        cap = SAFE_CONTEXT_CAP.get(family, DEFAULT_CAP)
        context_window = min(native_ctx, cap) if native_ctx else cap
        max_output = context_window // 4

    quant = details.get("quantization_level", "")
    label = "cloud proxy" if cloud else (quant or "local")

    return {
        "id": name,
        "name": f"{name} ({label})",
        "context_window": context_window,
        "max_output_tokens": max_output,
        "supports_reasoning": not non_gen,
        "supports_tools": not non_gen,
        "supports_streaming": not non_gen,
        "_notes": (
            f"native_context={native_ctx}; family={family}; "
            f"generated {date.today()}"
        ),
    }


def generate(base: str = "http://localhost:11434") -> dict:
    models = []
    for tag in get_tags(base):
        name: str = tag["name"]
        try:
            info = get_model_info(base, name)
            models.append(build_entry(name, info))
        except Exception as exc:  # noqa: BLE001
            print(f"# WARN: could not get info for {name}: {exc}", file=sys.stderr)

    return {
        "_comment": (
            f"Auto-generated {date.today()} by scripts/gen_local_models_json.py "
            "— do not edit manually. Regenerate when Ollama model list changes."
        ),
        "models": models,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--write", action="store_true",
        help="Write directly to ~/.codex/local_models.json (default: stdout)",
    )
    parser.add_argument(
        "--base", default="http://localhost:11434",
        help="Ollama base URL (default: http://localhost:11434)",
    )
    args = parser.parse_args()

    catalog = generate(args.base)
    output = json.dumps(catalog, indent=2)

    if args.write:
        dest = Path.home() / ".codex" / "local_models.json"
        dest.write_text(output + "\n", encoding="utf-8")
        print(f"Written to {dest}", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()
