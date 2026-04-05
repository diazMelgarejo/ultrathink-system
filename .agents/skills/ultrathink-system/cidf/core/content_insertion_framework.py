"""
content_insertion_framework.py
──────────────────────────────
Platform-agnostic core library for the Content Insertion Decision Framework v1.2.
All other Python-based integrations (LangChain, CrewAI) import from here.

No external dependencies required.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Protocol


# ─── Data models ──────────────────────────────────────────────────────────────

@dataclass
class Task:
    """Describes what needs to be done."""
    task_type: str                         # "content_insertion" | "automation" | "data_processing"
    is_one_time: bool
    frequency_estimate: int                # total estimated runs
    content_static: bool                   # True = no transformation or logic needed
    requires_transformation: bool
    requires_conditional_logic: bool
    requires_external_integration: bool
    content_length_chars: int
    format_requirements: str               # "plain" | "rich_text" | "strict_layout"
    signature: str                         # substring used to verify insertion


@dataclass
class Env:
    """Describes what methods are available in the current environment."""
    field_accessible: bool
    editor_visible: bool
    paste_supported: bool
    upload_available: bool
    max_safe_chars_form_input: int = 10_000
    max_safe_chars_typing: int = 5_000
    formatting_preserved_on_paste: bool = True


@dataclass
class Decision:
    """Output of decide(). Agent must execute chosen_tool then fallback_chain."""
    chosen_tool: str
    fallback_chain: List[str]
    reason_codes: List[str]
    automation_justified: bool
    verification_required: bool = True


@dataclass
class AttemptLog:
    tool: str
    result: str   # "success" | "verification_failed" | "no_executor_registered"


@dataclass
class ExecutionResult:
    status: str   # "success" | "failed"
    tool: str = ""
    attempts: List[AttemptLog] = field(default_factory=list)


# ─── Core logic ───────────────────────────────────────────────────────────────

def automation_justified(task: Task) -> bool:
    """
    Scripting ROI gate. Returns True only when at least one justification applies.
    Must return False for one-time static tasks regardless of other flags.
    """
    return (
        task.frequency_estimate >= 5
        or task.requires_conditional_logic
        or task.requires_transformation
        or task.requires_external_integration
    )


def decide(task: Task, env: Env) -> Decision:
    """
    Select the lowest-complexity eligible method.
    Enforces the priority order: form_input → typing → paste → upload → scripting.
    Scripting is added only when the automation gate is open AND it is the last resort.
    """
    reasons: List[str] = []
    tools: List[str] = []

    if env.field_accessible and task.content_length_chars <= env.max_safe_chars_form_input:
        tools.append("direct_form_input")
    if env.editor_visible and task.content_length_chars <= env.max_safe_chars_typing:
        tools.append("direct_typing")
    if env.paste_supported:
        tools.append("clipboard_paste")
    if env.upload_available:
        tools.append("file_upload")

    justified = automation_justified(task)
    if justified:
        tools.append("scripting")

    if not tools:
        tools = ["scripting"] if justified else ["direct_typing"]
        reasons.append("fallback_to_default_no_env_match")

    chosen = tools[0]
    fallback = tools[1:]

    # Hard block: never script a one-time static task
    if chosen == "scripting" and task.is_one_time and task.content_static:
        reasons.append("blocked_scripting_one_time_static")
        chosen = fallback[0] if fallback else "direct_typing"
        fallback = fallback[1:] if fallback else []

    reasons.append(f"chosen_{chosen}")
    reasons.append(f"automation_justified={justified}")

    return Decision(
        chosen_tool=chosen,
        fallback_chain=fallback,
        reason_codes=reasons,
        automation_justified=justified,
    )


# ─── Verification ─────────────────────────────────────────────────────────────

class Verifier(Protocol):
    """
    Implement this per environment (web/DOM, desktop, API).
    Never use visual confirmation as a substitute.
    """
    def refresh_once_if_needed(self) -> None: ...
    def extract_text(self) -> str: ...


def verify(verifier: Verifier, signature: str) -> bool:
    """
    Programmatic ground truth. Returns True only when signature
    is confirmed present in the extracted text.
    """
    verifier.refresh_once_if_needed()
    return signature in verifier.extract_text()


# ─── Execution loop ───────────────────────────────────────────────────────────

def execute_with_fallback(
    decision: Decision,
    executors: Dict[str, Callable[[str], None]],
    verifier: Verifier,
    content: str,
    signature: str,
) -> ExecutionResult:
    """
    Execute chosen_tool, then each fallback in order.
    Verify after each attempt. Return first success or full failure log.
    """
    chain = [decision.chosen_tool] + decision.fallback_chain
    attempts: List[AttemptLog] = []

    for tool in chain:
        executor = executors.get(tool)
        if executor is None:
            attempts.append(AttemptLog(tool=tool, result="no_executor_registered"))
            continue
        executor(content)
        if verify(verifier, signature):
            return ExecutionResult(status="success", tool=tool, attempts=attempts)
        attempts.append(AttemptLog(tool=tool, result="verification_failed"))

    return ExecutionResult(status="failed", attempts=attempts)
