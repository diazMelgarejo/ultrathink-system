---
name: ultrathink-system-skill
description: Master methodology for elegant problem solving. Unifies single_agent and multi_agent execution under the ultrathink 5-stage process. Routes automatically – runs inline for simple tasks (using CIDF v1.2 for any content insertion), escalates to the 7-agent network only when parallelism or scope demands it. Activates for any task requiring architectural thinking, systematic verification, content insertion decisions, or self-improvement.
version: 0.9.6.0
license: Apache 2.0
compatibility: claude-code, cowork, clawdbot, moltbot, openclaw, ecc-tools
allowed-tools: bash, file-operations, web-search, subagent-creation, mcp-ultrathink
---

# ultrathink System Skill

> *"Technology married with humanities yields solutions that make hearts sing. Every solution should feel inevitable — so elegant it couldn't be done any other way."*

---

## Execution Mode Router

ultrathink automatically selects between **CIDF (Single Agent)** and **Multi-Agent Network** modes based on complexity.

1.  **CIDF Mode (v1.2)**: Default for all coding, editing, and research tasks. Uses direct insertion for all content.
2.  **Multi-Agent Mode**: Activated for architectural design, complex bug hunting, or tasks requiring parallel execution.

---

## LAN Continuity & Reconciliation (Distributed State)

As part of the **v0.9.6.0** synchronization, ultrathink now supports **LAN Detect & Resume** in coordination with **Perplexity-Tools**.

### LAN Resume Logic
- **Detect & Re-attach**: On startup, ultrathink checks for an existing session on the LAN (Redis: `ultrathink:session:*`).
- **Short Logging**: Maintains minimal state logs in `.state/session.log` to allow resumption of complex 5-stage reasoning processes after interruption.
- **Distributed Discovery**: If a shared Redis is found (`REDIS_HOST`), state is synchronized globally; otherwise, local file-based state is used.

### Spawn Reconciliation (Layer 2 Coordination)
- **Global Registry Check**: Before spawning any sub-agent or worker, ultrathink MUST reconcile the spawn with the **Perplexity-Tools Orchestrator** (if available) to ensure proper session planning and model assignment.
- **Model-Aware Assignment**: Reconcile with the hardware registry to prevent GPU contention on machines like the `win-rtx3080` (Ollama/CUDA).
- **Efficient Operations**: Do not spawn new agents for subtasks if a matching idle agent exists in the global registry.

---

## Phase 1: Analyze & Design (Master Planning)
- **Goal**: Decompose user intent into a sequence of atomic, verifiable steps.
- **Rule**: Never start a task without an explicit design plan.
- **Output**: A structured TODO list in the conversation context.

## Phase 2: Execute & Implement (CIDF v1.2)
- **Goal**: Perform the work using the most efficient mode.
- **Method**: Favor `CIDF` for 90% of tasks; escalate to `Multi-Agent` for 10% high-complexity.

## Phase 3: Verify & Harden
- **Goal**: Ensure the solution meets the master plan.
- **Method**: Self-correction loop. If errors are found, return to Phase 1.

---

## Changelog

### v0.9.6.0 (2026-03-27)
- **LAN Continuity**: Synchronized **LAN Detect & Resume** logic with Perplexity-Tools.
- **Reconciliation**: Implemented **Layer 2 Spawn Reconciliation** to prevent redundant model spawns.
- **Distributed State**: Added support for shared Redis state for global session tracking across the LAN.
- **Hardening**: Reinforced phase transitions to be resume-aware.

### v0.9.4.3 (2026-03-24)
- Master methodology refinement and CIDF v1.2 standardization.
