

# ---------------------------------------------------------------------------
# CIDF Integration — Content Insertion Decision Framework v1.2
# All content writes MUST go through this wrapper
# ---------------------------------------------------------------------------

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "single_agent"))

try:
    from cidf.core.content_insertion_framework import (
        Task, Env, decide, execute_with_fallback, verify, Verifier
    )
    from cidf.linter.policy_linter import lint_strict, LintError
    CIDF_AVAILABLE = True
except ImportError:
    CIDF_AVAILABLE = False


def cidf_insert(
    content: str,
    signature: str,
    env_flags: dict,
    task_meta: dict,
    executor_fn: "dict[str, callable]",
    verifier: "Verifier",
) -> dict:
    """
    CIDF-compliant content insertion wrapper for executor agents.

    ALL content insertion in the multi-agent network goes through here.
    Never call a write/insert directly — always use this wrapper.

    Args:
        content:      The content to insert
        signature:    Unique string to verify insertion (e.g. a hash or marker)
        env_flags:    Dict with keys: field_accessible, editor_visible,
                      paste_supported, upload_available
        task_meta:    Dict with is_one_time, frequency_estimate, content_static,
                      requires_transformation, requires_conditional_logic,
                      requires_external_integration
        executor_fn:  Dict of {method_name: callable} for each rank
        verifier:     Object implementing refresh_once_if_needed() + extract_text()

    Returns:
        dict with status, cidf_version, chosen_tool, cidf_linted, cidf_verified
    """
    if not CIDF_AVAILABLE:
        raise RuntimeError(
            "CIDF package not found. Ensure single_agent/cidf/ is in the Python path."
        )

    task = Task(
        task_type="content_insertion",
        is_one_time=task_meta.get("is_one_time", True),
        frequency_estimate=task_meta.get("frequency_estimate", 1),
        content_static=task_meta.get("content_static", True),
        requires_transformation=task_meta.get("requires_transformation", False),
        requires_conditional_logic=task_meta.get("requires_conditional_logic", False),
        requires_external_integration=task_meta.get("requires_external_integration", False),
        content_length_chars=len(content),
        format_requirements=task_meta.get("format_requirements", "plain"),
        signature=signature,
    )

    env = Env(
        field_accessible=env_flags.get("field_accessible", False),
        editor_visible=env_flags.get("editor_visible", False),
        paste_supported=env_flags.get("paste_supported", False),
        upload_available=env_flags.get("upload_available", False),
    )

    # 1. Get CIDF decision (always starts at rank 1)
    decision = decide(task, env)

    # 2. Lint before executing (raises LintError on LINT-001–005)
    lint_strict(decision, task, env)

    # 3. Execute with automatic fallback + programmatic verification
    result = execute_with_fallback(
        decision=decision,
        executors=executor_fn,
        verifier=verifier,
        content=content,
        signature=signature,
    )

    return {
        "status":       result.status,
        "cidf_version": "1.2",
        "chosen_tool":  result.tool,
        "fallbacks_used": len(result.attempts),
        "cidf_linted":  True,
        "cidf_verified": result.status == "success",
    }
