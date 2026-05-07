# 03 — Safety Overlays (v2.5)

> Status: stub. Designed for v2.5; kernel-aware in v2.0 but enforcement is non-blocking.

---

## Why a separate version

MAESTRO and SWARM are heavyweight enough to warrant their own release vehicle. Bundling them with v2.0 would either (a) inflate the kernel beyond microkernel ethos, or (b) ship them half-baked. Splitting into v2.5 lets v2.0 ship first with kernel hooks (HITL `Interrupt`, GossipBus event log, structured output validation) — the safety overlays then *use* those hooks rather than reinventing them.

---

## MAESTRO 7-layer threat modeling

Source: Perplexity. Layers cover the multi-agent threat surface from goal misalignment down to subprocess privilege.

| # | Layer | v2.0 kernel hook | v2.5 enforcement |
|---|-------|------------------|------------------|
| 1 | Goal alignment | `PerpetuaState.opt_hint` + task_type | Goal verifier subgraph; HITL on mismatch |
| 2 | Plan integrity | `nodes_visited` audit trail | Plan diffing across runs; alert on drift |
| 3 | Agent identity | `metadata["agent_id"]` | Cryptographic agent attestation per node |
| 4 | Tool authority | ToolNode subprocess sandbox | Per-tool allowlist + capability tokens |
| 5 | Data provenance | `messages` history immutable | Provenance graph (input → output traces) |
| 6 | Hardware affinity | `HardwarePolicyResolver` (kernel) | already enforced in kernel ✅ |
| 7 | Human oversight | `Interrupt` + checkpointer (kernel) | HITL gates auto-injected at MAESTRO-defined chokepoints |

Layer 6 is already kernel-enforced per D4 (the non-negotiable). Layers 1–5 + 7 build on kernel primitives.

---

## SWARM (System-Wide Assessment of Risk in Multi-agent systems)

Source: Perplexity. Misalignment guardrails for emergent multi-agent risk — catastrophic failures emerge from interactions between agents, not from individual models.

### Components (v2.5 deliverables)

- **Aggregate risk scoring** — every agent dispatch contributes a risk score; SWARM aggregates across the graph.
- **Cross-agent contradiction detection** — flags when two agents reach contradictory conclusions on the same input.
- **Misalignment kill-switch** — when aggregate risk exceeds threshold, raise `Interrupt` and demand human approval.
- **Audit replay** — given a session_id, replay the exact sequence of GossipBus events into a deterministic risk timeline.

### Kernel hooks SWARM relies on

- `GossipBus` events: every kernel operation (load, route, affinity_check, dispatch, error) is already recorded → audit replay works for free.
- `Interrupt` mechanism: kill-switch is just an `Interrupt` raised by a SWARM monitor node sitting in the graph.
- `PerpetuaState.metadata["risk_score"]` reducer: SWARM monitor accumulates per-node risk into state.

---

## Human Accountability Framework

> These five rules are the **foundational accountability layer** that MAESTRO and SWARM operate within. They are generalised from established AI governance frameworks — including EU AI Act 2024 human-oversight requirements (Art. 12–15), NIST AI Risk Management Framework, and Anthropic's Constitutional AI principles — and operationalised as concrete v2 kernel constraints and v2.5 enforcement policies. They apply regardless of deployment context, performance requirements, or user-granted permissions.

### The five rules

| # | Rule | v2.0 kernel primitive | v2.5 enforcement |
|---|------|-----------------------|------------------|
| R1 | **No harmful action** — a system shall not perform any action that could harm humanity, individuals, societal structures, or the environment, even if that action aligns with pre-set objectives or programmed tasks | `HardwarePolicyResolver` NEVER verdict raises before spawn; `MiniGraph` `max_steps` guard prevents runaway loops | MAESTRO Layer 1 goal-verifier subgraph; per-ToolNode capability allowlist (MAESTRO Layer 4); SWARM aggregate risk threshold kill-switch |
| R2 | **Human authorization and accountability** — a system shall require human authorization before executing any consequential command; authorizers bear full accountability as if they had personally committed the acts | `Interrupt` prompt carries `required_auth: True`; `GossipBus` records `authorization` event with `actor_id` before any consequential dispatch; checkpointer persists state until approval is received | MAESTRO Layer 7 HITL gate auto-injected at every consequential chokepoint; `/audit/session/{id}` endpoint exposes full authorization chain |
| R3 | **No override obstruction** — a system shall not obstruct or bypass human intervention; a manual override path must always exist and must not be blockable by code | `Interrupt` is always-escapable: `aresume(override=True)` from a human-authenticated caller terminates the interrupt unconditionally; `status="interrupted"` and `status="conflicted"` are terminal-until-human — no code path in the kernel may clear them except `aresume` | SWARM kill-switch raises `Interrupt` — same path, same escape hatch; v2.5 adds `override_audit` GossipBus event recording every manual override with timestamp and caller identity |
| R4 | **Transparent audit log** — a system shall maintain a clear and transparent log of its decision-making processes and actions, accessible at all times to all authorized operators | `GossipBus` records every kernel operation (`load`, `route`, `affinity_check`, `dispatch`, `error`, `authorization`, `override`); SQLite — append-only, queryable by any operator with file access; `nodes_visited` on state for in-flight traceability | SWARM audit replay: deterministic risk timeline from GossipBus events; v2.5 `/audit/session/{id}` HTTP endpoint returns full event log as JSON |
| R5 | **Conflict escalation to humans** — when guidelines conflict, the system shall pause, alert operators, and defer; the operators who resolve the conflict bear ultimate responsibility | `PerpetuaState.status = "conflicted"` (first-class status alongside `"interrupted"`); conflict-detection edge raises `Interrupt(prompt=..., payload={"conflicting_rules": [...]})` before any action is taken | SWARM cross-agent contradiction detection triggers `"conflicted"` state; v2.5 adds multi-operator notification channel (configurable: GossipBus subscribe + webhook endpoint) |

### Mapping to EU AI Act (2024) requirements

The EU AI Act imposes human oversight (Art. 14), traceability (Art. 12), operator transparency (Art. 13), and accuracy/robustness standards (Art. 15) on high-risk AI systems. The v2 kernel primitives satisfy each requirement directly:

| EU AI Act article | Requirement | v2 primitive | File |
|-------------------|-------------|--------------|------|
| Art. 14 | Human oversight measures | `Interrupt` + `aresume` + HITL gate | `graph/interrupts.py` |
| Art. 12 | Traceability and logging | `GossipBus` append-only event log + `nodes_visited` | `gossip.py`, `state.py` |
| Art. 13 | Operator transparency | `/audit` API + GossipBus subscription iterator | `oramasys/api/server.py` |
| Art. 15 | Accuracy and robustness | `HardwarePolicyResolver` hard gate + `max_steps` guard | `policy.py`, `engine.py` |

> **Classification note**: Whether a given perpetua-core deployment qualifies as "high-risk" under the EU AI Act depends on the deployment context and must be determined by the system builder. These primitives are designed to satisfy high-risk requirements proactively, regardless of eventual classification.

### Key design constraints flowing from the five rules

These are **v2.0 kernel constraints**, not v2.5 aspirations. They must pass the verification criteria in `01-kernel-spec.md` (items 11–13) before any release:

1. **`Interrupt` is always-escapable (R3)**: No node, plugin, or SWARM monitor may catch `Interrupt` internally and suppress it. `Interrupt` propagates to the engine, which sets `status="interrupted"` and returns to the caller. Only `aresume()` with a human-supplied payload may resume execution.

2. **`GossipBus` is append-only by default (R4)**: The default `GossipBus` implementation exposes no `delete`, `update`, or `truncate` method. All events are permanent. An operator with read access to `perpetua_core.db` can always reconstruct the full decision trail without relying on the system being online.

3. **Authorization events are mandatory before consequential ToolNode dispatch (R2)**: Any `ToolNode` that executes a subprocess with external side effects MUST emit a `GossipBus` `authorization` event before the subprocess call. The payload must include `actor_id` (who authorized) and `tool_cmd` (what was authorized). Read-only subprocess nodes are exempt.

4. **`status="conflicted"` is a first-class state (R5)**: Treated identically to `"interrupted"` by the engine — the graph halts and checkpoints. Resumption requires `aresume(conflict_resolution=...)`. The resolution payload is recorded in `metadata["conflict_resolution"]` on the resulting state.

---

## Sequencing relative to other modules

- **v2.0**: kernel hooks land. No safety enforcement code yet. MAESTRO + SWARM kept off-graph.
- **v2.1**: public Plugin API stabilizes. Still no safety enforcement.
- **v2.5**: MAESTRO enforcement subgraphs + SWARM monitor node land as a single non-kernel package (`perpetua-safety` or similar). Composable into any oramasys graph.

---

## Open design questions

- Does `perpetua-safety` ship as a separate repo or a subpackage of `perpetua-core`? (Likely separate — keeps kernel pure.)
- How does the misalignment kill-switch interact with `aresume`? (Probably: only human-supplied `aresume` payloads can clear a SWARM-raised interrupt.)
- What's the interface for "agent identity attestation" (MAESTRO layer 3)? Cryptographic? Cached per-process? See `06-open-questions.md`.
