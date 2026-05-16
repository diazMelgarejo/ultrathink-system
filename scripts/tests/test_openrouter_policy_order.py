"""OpenRouter policy ordering tests.

These tests pin the intended merge/verify behavior so Gemini cannot creep back
into the default fallback chain ahead of OpenRouter.
"""
from __future__ import annotations

import json
import re
from pathlib import Path


REPO_ROOT = Path(__file__).parent.parent.parent
POLICY_PATH = REPO_ROOT / "deployments" / "macbook-pro-head" / "openclaw" / "openclaw.model-policy.jsonc"
APPLY_SCRIPT = REPO_ROOT / "scripts" / "apply-openrouter-free-defaults.sh"
VERIFY_SCRIPT = REPO_ROOT / "scripts" / "verify-openrouter-models.sh"


def _load_jsonc(path: Path) -> dict:
    raw = path.read_text(encoding="utf-8")
    stripped = re.sub(r"(?m)^[ \t]*//.*$", "", raw)
    stripped = re.sub(r"(?<!:)//[^\n]*$", "", stripped)
    return json.loads(stripped)


def test_policy_places_openrouter_before_gemini():
    policy = _load_jsonc(POLICY_PATH)
    fallbacks = policy["agents"]["defaults"]["model"]["fallbacks_to_merge"]

    assert "openrouter/openrouter/free" in fallbacks
    assert "google/gemini-2.5-pro" in fallbacks
    assert "google/gemini-2.5-flash" in fallbacks
    assert fallbacks.index("openrouter/openrouter/free") < fallbacks.index("google/gemini-2.5-pro")
    assert fallbacks.index("google/gemini-2.5-pro") < fallbacks.index("google/gemini-2.5-flash")


def test_policy_only_merges_openrouter_models_into_allowlist():
    policy = _load_jsonc(POLICY_PATH)
    models_to_merge = policy["agents"]["defaults"]["models_to_merge"]

    assert all(key.startswith("openrouter/") for key in models_to_merge)
    assert not any("gemini" in key.lower() for key in models_to_merge)


def test_apply_script_strips_gemini_from_existing_fallbacks():
    script = APPLY_SCRIPT.read_text(encoding="utf-8")
    policy = _load_jsonc(POLICY_PATH)

    assert 'test("(^|/)gemini"; "i")' in script
    assert "fallbacks_to_merge" in script
    assert "openrouter/openrouter/free" in policy["agents"]["defaults"]["model"]["fallbacks_to_merge"]


def test_verify_script_checks_openrouter_before_gemini():
    script = VERIFY_SCRIPT.read_text(encoding="utf-8")

    assert "first_nonlocal" in script
    assert "first_openrouter_index" in script
    assert "first_gemini_index" in script
    assert "Gemini relegated behind OpenRouter" in script
