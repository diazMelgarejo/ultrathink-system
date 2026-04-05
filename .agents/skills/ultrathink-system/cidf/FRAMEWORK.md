# Content Insertion Decision Framework
**Version:** 1.2 | **License:** Apache 2.0 | **Updated:** 2026-03-20
**Single source of truth:** `content_insertion_policy.json`

---

## PART 1 — MASTER PLAYBOOK

### The One Rule
> **Use the simplest tool that works. Complexity is a cost, not a feature.**

---

### Task Classification

Before choosing any method, classify the task on two axes:

| Axis | Options |
|------|---------|
| Recurrence | one-time · repeatable (≥ 5 uses) |
| Content nature | static · needs logic · needs transformation · needs external integration |

Default assumption: **one-time, static** → use simplicity-first mode.

---

### Method Priority Order (Universal)

Always iterate top-to-bottom. Stop at the **first eligible method.**

| Rank | Method | Max Content | Key Requirement |
|------|--------|-------------|-----------------|
| 1 | `direct_form_input` | 10 000 chars | `field_accessible == true` |
| 2 | `direct_typing` | 5 000 chars | `editor_visible == true` |
| 3 | `clipboard_paste` | No limit | `paste_supported == true` |
| 4 | `file_upload` | No limit | `upload_available == true` |
| 5 | `scripting` | No limit | **Automation gate must pass** |

---

### Automation Gate

Scripting is **only eligible** when the gate is **open**:

```
OPEN  (any one true):   frequency ≥ 5
                        requires_conditional_logic
                        requires_transformation
                        requires_external_integration

CLOSED (any one true):  is_one_time AND content_static
                        ANY rank 1–4 method is eligible
```

When the gate is closed and all ranks 1–4 fail: **notify the user — do not script.**

---

### Verification Protocol (Mandatory)

Visual confirmation is **insufficient**. Pages lag. Caches lie.

```
1. Execute chosen method
2. Wait for UI response
3. If no visual change → refresh page once
4. Extract text programmatically (read_page / DOM query / API fetch)
5. Check that task.signature is present in extracted text
6. If present  → log success, mark complete
7. If absent   → log failure, try next method in fallback_chain
8. If chain exhausted → notify user with full failure log
```

---

### Anti-Patterns (Block These)

| Anti-Pattern | Detection | Fix |
|---|---|---|
| **Premature scripting** | scripting chosen while ranks 1–4 eligible | Iterate from rank 1 |
| **Visual assumption** | complete marked without programmatic check | Always call extract_text |
| **Complexity bias** | higher-complexity tool chosen without exhausting lower ranks | Trust priority order |
| **Failure escalation** | jumping to scripting after one failure | Exhaust full fallback chain first |

---

### Quick Reference Card

```
┌──────────────────────────────────────────────────────────┐
│           CONTENT INSERTION — DECISION CARD              │
│                                                          │
│  RANK  METHOD              STOP WHEN ELIGIBLE            │
│  1  →  form_input          field accessible + ≤10k       │
│  2  →  direct_typing       editor visible  + ≤5k         │
│  3  →  clipboard_paste     paste supported               │
│  4  →  file_upload         upload available              │
│  5  →  scripting           GATE OPEN only                │
│                                                          │
│  SCRIPTING RED FLAGS    │  SCRIPTING GREEN LIGHTS        │
│  ⛔ One-time + static   │  ✅ Runs 5+ times              │
│  ⛔ Simpler tool exists  │  ✅ Logic required             │
│  ⛔ Setup > run time     │  ✅ Transformation needed      │
│                         │  ✅ External integration        │
│                                                          │
│  VERIFY: execute → refresh? → extract_text → signature   │
└──────────────────────────────────────────────────────────┘
```

---

## PART 2 — SKILL SETS (Explicit Per-Platform Instructions)

Each skill set below is a **self-contained, step-by-step implementation guide** for one platform. All share the same `content_insertion_policy.json` as their single source of truth.

---

### SKILL SET 1 — Python (Platform-Agnostic Core Library)

**Purpose:** Reference implementation. All other Python-based skills import from this.
**File:** `core/content_insertion_framework.py`

#### Step-by-Step Instructions

**Step 1 — Install dependencies**
```bash
# No external deps required for the core library
# Optional for typed checking:
pip install mypy
```

**Step 2 — Define data models**

Use `@dataclass` for all inputs and outputs. Never use plain dicts in production — type safety prevents misrouted decisions.

```python
from dataclasses import dataclass, field
from typing import List

@dataclass
class Task:
    task_type: str                       # "content_insertion" | "automation" | "data_processing"
    is_one_time: bool
    frequency_estimate: int              # how many times this task will run total
    content_static: bool                 # True = no transformation/logic needed
    requires_transformation: bool        # True = format, template, or parse step needed
    requires_conditional_logic: bool     # True = branching rules needed
    requires_external_integration: bool  # True = calls external API or system
    content_length_chars: int
    format_requirements: str             # "plain" | "rich_text" | "strict_layout"
    signature: str                       # substring present in content; used for verification

@dataclass
class Env:
    field_accessible: bool               # form field reachable via DOM/API
    editor_visible: bool                 # text editor in viewport
    paste_supported: bool                # clipboard paste permitted
    upload_available: bool               # file upload endpoint exists
    max_safe_chars_form_input: int = 10_000
    max_safe_chars_typing: int = 5_000
    formatting_preserved_on_paste: bool = True

@dataclass
class Decision:
    chosen_tool: str
    fallback_chain: List[str]
    reason_codes: List[str]
    automation_justified: bool
    verification_required: bool = True
```

**Step 3 — Implement the automation gate**

```python
def automation_justified(task: Task) -> bool:
    """
    Returns True only when scripting ROI is real.
    This gate is checked BEFORE scripting is added to the tool list.
    """
    return (
        task.frequency_estimate >= 5
        or task.requires_conditional_logic
        or task.requires_transformation
        or task.requires_external_integration
    )
```

**Step 4 — Implement the decision function**

```python
def decide(task: Task, env: Env) -> Decision:
    reasons: List[str] = []
    tools: List[str] = []

    # Build eligible list in priority order — NEVER skip or reorder
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

    # Fallback if nothing qualifies (edge case)
    if not tools:
        tools = ["scripting"] if justified else ["direct_typing"]
        reasons.append("fallback_to_default_no_env_match")

    chosen = tools[0]
    fallback = tools[1:]

    # Hard block: prevent scripting for one-time static content
    if chosen == "scripting" and task.is_one_time and task.content_static:
        reasons.append("blocked_scripting_one_time_static")
        chosen = fallback[0] if fallback else "direct_typing"
        fallback = fallback[1:] if fallback else []

    reasons.append(f"chosen_{chosen}")
    reasons.append(f"automation_justified={justified}")
    return Decision(chosen, fallback, reasons, justified)
```

**Step 5 — Implement verification**

```python
from typing import Protocol

class Verifier(Protocol):
    def refresh_once_if_needed(self) -> None: ...
    def extract_text(self) -> str: ...

def verify(verifier: Verifier, signature: str) -> bool:
    """
    Always call this after executing a method.
    Returns True only when signature is confirmed in extracted text.
    """
    verifier.refresh_once_if_needed()
    text = verifier.extract_text()
    return signature in text
```

**Step 6 — Wire into execution loop**

```python
from typing import Callable

def execute_with_fallback(
    decision: Decision,
    executors: dict[str, Callable[[str], None]],
    verifier: Verifier,
    content: str,
    signature: str,
) -> dict:
    """
    Tries chosen_tool, then each fallback in order.
    Verifies after each attempt. Returns result log.
    """
    attempts = []
    for tool in [decision.chosen_tool] + decision.fallback_chain:
        executor = executors.get(tool)
        if executor is None:
            attempts.append({"tool": tool, "result": "no_executor_registered"})
            continue
        executor(content)
        if verify(verifier, signature):
            return {"status": "success", "tool": tool, "attempts": attempts}
        attempts.append({"tool": tool, "result": "verification_failed"})
    return {"status": "failed", "attempts": attempts, "action": "notify_user"}
```

**Key Rules for this skill:**
- Never import from agent frameworks in the core library — it must be framework-agnostic
- Always pass `signature` through from the original task — never generate it in the verifier
- The `Verifier` protocol must be implemented per-environment (web, desktop, API)

---

### SKILL SET 2 — LangChain (Python)

**Purpose:** Wrap the core library as a LangChain Tool, usable by any LangChain agent.
**Files:** `skills/langchain/insert_policy_tool.py`, `skills/langchain/langchain_agent.py`
**Requires:** `pip install langchain langchain-openai`

#### Step-by-Step Instructions

**Step 1 — Import core library**

```python
# skills/langchain/insert_policy_tool.py
from __future__ import annotations
import sys
sys.path.insert(0, "../../")          # point to cidf root
from core.content_insertion_framework import Task, Env, decide, verify, automation_justified
```

**Step 2 — Create the @tool function**

LangChain tools must:
- Accept a single `dict` argument (JSON-serialisable)
- Return a JSON-serialisable `dict`
- Have a clear `description` the LLM uses to decide when to call it

```python
from langchain.tools import tool

@tool("content_insertion_decider")
def content_insertion_decider(payload: dict) -> dict:
    """
    Decide the optimal content insertion method given task and environment properties.
    Call this BEFORE attempting any content insertion action.
    Input: {"task": {...Task fields...}, "env": {...Env fields...}}
    Output: {"chosen_tool": str, "fallback_chain": list, "reason_codes": list,
             "automation_justified": bool, "verification_required": true}
    """
    task = Task(**payload["task"])
    env  = Env(**payload["env"])
    d    = decide(task, env)
    return {
        "chosen_tool":          d.chosen_tool,
        "fallback_chain":       d.fallback_chain,
        "reason_codes":         d.reason_codes,
        "automation_justified": d.automation_justified,
        "verification_required": d.verification_required,
    }
```

**Step 3 — Create the agent with the tool**

```python
# skills/langchain/langchain_agent.py
from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate
from insert_policy_tool import content_insertion_decider

SYSTEM_PROMPT = """
You are a content insertion agent. You follow the Content Insertion Decision Framework v1.2.

RULES:
1. Before inserting any content, call content_insertion_decider with task + env details.
2. Execute the chosen_tool method first.
3. If it fails, try each tool in fallback_chain in order.
4. ALWAYS verify with extract_text — never mark complete on visual confirmation alone.
5. Never choose scripting unless automation_justified is true.
"""

llm   = ChatOpenAI(model="gpt-4o-mini", temperature=0)
tools = [content_insertion_decider]
prompt = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    ("human", "{input}"),
    ("placeholder", "{agent_scratchpad}"),
])
agent = create_tool_calling_agent(llm, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
```

**Step 4 — Run the agent**

```python
result = agent_executor.invoke({
    "input": """
    Insert the following article into the CMS text field:
    TASK: is_one_time=true, frequency=1, static=true, length=2000 chars
    ENV:  field_accessible=true, editor_visible=true, paste_supported=true
    SIGNATURE: 'article_marker_abc123'
    CONTENT: <your content here>
    """
})
```

**Key Rules for this skill:**
- Always include `verification_required: true` in the tool's response — the LLM must be reminded
- Set `temperature=0` on the LLM — deterministic behaviour is critical for policy compliance
- Add the anti-pattern descriptions to the system prompt so the LLM recognises them

---

### SKILL SET 3 — CrewAI (Python)

**Purpose:** Assign the decision framework as a shared tool across a multi-agent crew.
**Files:** `skills/crewai/crewai_setup.py`
**Requires:** `pip install crewai langchain`

#### Step-by-Step Instructions

**Step 1 — Reuse the LangChain tool**

CrewAI accepts LangChain-format tools directly. Import from Skill Set 2:

```python
from skills.langchain.insert_policy_tool import content_insertion_decider
```

**Step 2 — Define the inserter agent**

```python
from crewai import Agent

inserter_agent = Agent(
    role="Content Insertion Specialist",
    goal=(
        "Insert content into documents or web fields with minimal complexity. "
        "Always follow the simplicity-first priority order. Always verify programmatically."
    ),
    backstory=(
        "You are a precise, rule-following agent trained on the Content Insertion "
        "Decision Framework v1.2. You never assume visual confirmation is sufficient. "
        "You never use scripting when a simpler method is available."
    ),
    tools=[content_insertion_decider],
    verbose=True,
    allow_delegation=False,   # this agent owns insertion decisions completely
)
```

**Step 3 — Define the verification agent (optional, recommended for high-stakes tasks)**

```python
verifier_agent = Agent(
    role="Content Verification Specialist",
    goal="Confirm that content was inserted correctly using programmatic text extraction.",
    backstory=(
        "You complete every task by extracting page text and confirming the expected "
        "signature is present. You never trust UI visuals."
    ),
    tools=[],   # verifier only reads; receives extracted text from environment
    verbose=True,
)
```

**Step 4 — Define tasks**

```python
from crewai import Task as CrewTask

decision_task = CrewTask(
    description=(
        "Given the following task and environment properties, decide the correct "
        "insertion method and produce an execution plan:\n"
        "task={task_json}\n"
        "env={env_json}\n"
        "You MUST call content_insertion_decider. "
        "Output: chosen_tool, fallback_chain, verification steps."
    ),
    expected_output=(
        "JSON with: chosen_tool, fallback_chain, reason_codes, "
        "automation_justified, verification_required"
    ),
    agent=inserter_agent,
)

verification_task = CrewTask(
    description=(
        "Verify that the signature '{signature}' is present in the current page text. "
        "Extract page text programmatically, search for the signature, and report PASS or FAIL."
    ),
    expected_output="{'verification': 'PASS' | 'FAIL', 'signature_found': bool}",
    agent=verifier_agent,
    context=[decision_task],   # depends on decision task completing first
)
```

**Step 5 — Assemble and run the crew**

```python
from crewai import Crew, Process

crew = Crew(
    agents=[inserter_agent, verifier_agent],
    tasks=[decision_task, verification_task],
    process=Process.sequential,  # decision must complete before verification
    verbose=True,
)

result = crew.kickoff(inputs={
    "task_json": '{"is_one_time": true, "frequency_estimate": 1, ...}',
    "env_json":  '{"field_accessible": true, ...}',
    "signature": "article_marker_abc123",
})
```

**Key Rules for this skill:**
- Always use `Process.sequential` — verification must follow execution, never be parallel
- Set `allow_delegation=False` on the inserter agent — the decision belongs to it alone
- Pass `context=[decision_task]` on verification so it receives the chosen tool output

---

### SKILL SET 4 — TypeScript (Platform-Agnostic Library)

**Purpose:** Reference implementation for all TypeScript/Node.js agent frameworks.
**File:** `skills/typescript/contentInsertionFramework.ts`
**Requires:** `npm install typescript` (no runtime deps)

#### Step-by-Step Instructions

**Step 1 — Define strict types**

```typescript
// skills/typescript/types.ts
export type TaskType = "content_insertion" | "automation" | "data_processing";
export type FormatRequirement = "plain" | "rich_text" | "strict_layout";
export type ToolName = "direct_form_input" | "direct_typing" | "clipboard_paste" | "file_upload" | "scripting";

export interface Task {
  task_type: TaskType;
  is_one_time: boolean;
  frequency_estimate: number;
  content_static: boolean;
  requires_transformation: boolean;
  requires_conditional_logic: boolean;
  requires_external_integration: boolean;
  content_length_chars: number;
  format_requirements: FormatRequirement;
  signature: string;             // substring to verify insertion succeeded
}

export interface Env {
  field_accessible: boolean;
  editor_visible: boolean;
  paste_supported: boolean;
  upload_available: boolean;
  max_safe_chars_form_input?: number;   // default 10000
  max_safe_chars_typing?: number;       // default 5000
  formatting_preserved_on_paste?: boolean;
}

export interface Decision {
  chosen_tool: ToolName;
  fallback_chain: ToolName[];
  reason_codes: string[];
  automation_justified: boolean;
  verification_required: true;
}

export interface Verifier {
  refreshOnceIfNeeded(): Promise<void>;
  extractText(): Promise<string>;
}

export interface ExecutionResult {
  status: "success" | "failed";
  tool?: ToolName;
  attempts: Array<{ tool: ToolName; result: string }>;
}
```

**Step 2 — Implement automation gate and decision function**

```typescript
// skills/typescript/contentInsertionFramework.ts
import { Task, Env, Decision, ToolName, Verifier, ExecutionResult } from "./types";

export function automationJustified(task: Task): boolean {
  return (
    task.frequency_estimate >= 5 ||
    task.requires_conditional_logic ||
    task.requires_transformation ||
    task.requires_external_integration
  );
}

export function decide(task: Task, env: Env): Decision {
  const maxForm   = env.max_safe_chars_form_input ?? 10_000;
  const maxTyping = env.max_safe_chars_typing ?? 5_000;

  const reasons: string[] = [];
  const tools: ToolName[] = [];

  if (env.field_accessible && task.content_length_chars <= maxForm)   tools.push("direct_form_input");
  if (env.editor_visible   && task.content_length_chars <= maxTyping) tools.push("direct_typing");
  if (env.paste_supported)   tools.push("clipboard_paste");
  if (env.upload_available)  tools.push("file_upload");

  const justified = automationJustified(task);
  if (justified) tools.push("scripting");

  if (tools.length === 0) {
    tools.push(justified ? "scripting" : "direct_typing");
    reasons.push("fallback_to_default_no_env_match");
  }

  let chosen   = tools[0];
  let fallback = tools.slice(1) as ToolName[];

  if (chosen === "scripting" && task.is_one_time && task.content_static) {
    reasons.push("blocked_scripting_one_time_static");
    chosen   = fallback[0] ?? "direct_typing";
    fallback = fallback.slice(1);
  }

  reasons.push(`chosen_${chosen}`);
  reasons.push(`automation_justified=${justified}`);

  return {
    chosen_tool: chosen,
    fallback_chain: fallback,
    reason_codes: reasons,
    automation_justified: justified,
    verification_required: true,
  };
}
```

**Step 3 — Implement verification**

```typescript
export async function verify(verifier: Verifier, signature: string): Promise<boolean> {
  await verifier.refreshOnceIfNeeded();
  const text = await verifier.extractText();
  return text.includes(signature);
}
```

**Step 4 — Implement execution loop**

```typescript
export async function executeWithFallback(
  decision: Decision,
  executors: Partial<Record<ToolName, (content: string) => Promise<void>>>,
  verifier: Verifier,
  content: string,
  signature: string,
): Promise<ExecutionResult> {
  const chain = [decision.chosen_tool, ...decision.fallback_chain];
  const attempts: ExecutionResult["attempts"] = [];

  for (const tool of chain) {
    const executor = executors[tool];
    if (!executor) {
      attempts.push({ tool, result: "no_executor_registered" });
      continue;
    }
    await executor(content);
    const ok = await verify(verifier, signature);
    if (ok) return { status: "success", tool, attempts };
    attempts.push({ tool, result: "verification_failed" });
  }

  return { status: "failed", attempts };
}
```

**Step 5 — Implement a concrete Verifier for browser/DOM**

```typescript
// skills/typescript/domVerifier.ts
import { Verifier } from "./types";

export class DomVerifier implements Verifier {
  private visualChangeSeen = false;

  async refreshOnceIfNeeded(): Promise<void> {
    if (!this.visualChangeSeen) {
      await new Promise(r => setTimeout(r, 500));  // wait for DOM settle
      window.location.reload();
      await new Promise(r => setTimeout(r, 1000));
    }
  }

  async extractText(): Promise<string> {
    return document.body.innerText ?? "";
  }
}
```

**Key Rules for this skill:**
- Export all types from a central `types.ts` — never duplicate type definitions across files
- The `Verifier` interface is the extension point — implement it per environment (DOM, API, Playwright)
- Never `await` visual indicators; always `await verifier.extractText()` as the ground truth

---

### SKILL SET 5 — OpenClaw (Node.js / TypeScript)

**Purpose:** Integrate the framework as a skill handler in an OpenClaw bot.
**Files:** `skills/openclaw/contentInsertionSkill.ts`
**Requires:** OpenClaw SDK + TypeScript library from Skill Set 4

#### Step-by-Step Instructions

**Step 1 — Import core types and decision function**

```typescript
// skills/openclaw/contentInsertionSkill.ts
import { decide, automationJustified, verify } from "../typescript/contentInsertionFramework";
import { Task, Env, Decision, Verifier } from "../typescript/types";
```

**Step 2 — Define the skill handler**

OpenClaw skills receive a `ctx` context object. Map its properties to `Task` and `Env`:

```typescript
export interface OpenClawContentCtx {
  task: Task;
  env: Env;
  content: string;
  verifier: Verifier;
  log: { info: (msg: string, data?: any) => void; error: (msg: string, data?: any) => void };
  ui: {
    formInput:  (selector: string, content: string) => Promise<void>;
    type:       (content: string) => Promise<void>;
    paste:      (content: string) => Promise<void>;
    upload:     (filePath: string) => Promise<void>;
  };
  scripting: {
    run: (content: string) => Promise<void>;
  };
}
```

**Step 3 — Map tool names to executor functions**

```typescript
function buildExecutors(ctx: OpenClawContentCtx, selector?: string) {
  return {
    direct_form_input: async (c: string) => ctx.ui.formInput(selector ?? "input,textarea", c),
    direct_typing:     async (c: string) => ctx.ui.type(c),
    clipboard_paste:   async (c: string) => ctx.ui.paste(c),
    file_upload:       async (c: string) => ctx.ui.upload(c),  // c is file path for upload
    scripting:         async (c: string) => ctx.scripting.run(c),
  };
}
```

**Step 4 — Implement the skill handler**

```typescript
import { executeWithFallback } from "../typescript/contentInsertionFramework";

export async function handleContentInsertion(
  ctx: OpenClawContentCtx,
  selector?: string,
): Promise<{ status: string; tool?: string; attempts: any[] }> {
  const decision = decide(ctx.task, ctx.env);
  ctx.log.info("content_insertion_decision", { decision });

  const executors = buildExecutors(ctx, selector);
  const result = await executeWithFallback(
    decision,
    executors,
    ctx.verifier,
    ctx.content,
    ctx.task.signature,
  );

  if (result.status === "failed") {
    ctx.log.error("all_insertion_methods_failed", { attempts: result.attempts });
  } else {
    ctx.log.info("insertion_succeeded", { tool: result.tool });
  }

  return result;
}
```

**Step 5 — Register as an OpenClaw skill**

```typescript
// skills/openclaw/register.ts
import { handleContentInsertion } from "./contentInsertionSkill";

export const contentInsertionSkill = {
  id: "content_insertion",
  name: "Content Insertion (Decision Framework v1.2)",
  description: "Insert content into documents or UI fields using simplicity-first method selection.",
  handler: handleContentInsertion,
  policyRef: "../../core/content_insertion_policy.json",
};
```

**Key Rules for this skill:**
- Always pass `ctx.log` calls through — OpenClaw relies on structured logs for replay debugging
- The `selector` argument is optional — fall back to generic `"input,textarea"` for form_input
- Register `policyRef` so the OpenClaw dashboard can display the governing policy version

---

## PART 3 — CONFORMANCE RULES

Any implementation passes conformance if and only if all 6 test vectors produce the expected `chosen_tool`. See `tests/` for runnable test suites.

| TV | Scenario | Expected Tool |
|----|----------|---------------|
| TV-01 | 2k chars, field accessible | `direct_form_input` |
| TV-02 | 12k chars, field over limit | `clipboard_paste` |
| TV-03 | Rich text, typing available | `direct_typing` |
| TV-04 | No field/editor/paste, upload available | `file_upload` |
| TV-05 | Repeatable + logic, but field accessible | `direct_form_input` |
| TV-06 | UI lag — verify before marking complete | `direct_form_input` + refresh behavior |

---

## PART 4 — LINTING RULES

A policy linter must reject any `Decision` that violates:

| Rule ID | Violation | Message |
|---------|-----------|---------|
| `LINT-001` | scripting chosen while rank 1–4 eligible | "Simpler method available; scripting blocked" |
| `LINT-002` | `verification_required` missing or false | "Verification is mandatory; cannot be disabled" |
| `LINT-003` | chosen_tool complexity > minimum eligible | "Complexity bias detected; use lower-rank tool" |
| `LINT-004` | scripting chosen for one-time static task | "Scripting gate closed: one-time static content" |
| `LINT-005` | fallback_chain empty when failure is likely | "No fallback defined; add at least one fallback" |
