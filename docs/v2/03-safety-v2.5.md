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

## Sequencing relative to other modules

- **v2.0**: kernel hooks land. No safety enforcement code yet. MAESTRO + SWARM kept off-graph.
- **v2.1**: public Plugin API stabilizes. Still no safety enforcement.
- **v2.5**: MAESTRO enforcement subgraphs + SWARM monitor node land as a single non-kernel package (`perpetua-safety` or similar). Composable into any oramasys graph.

---

## Open design questions

- Does `perpetua-safety` ship as a separate repo or a subpackage of `perpetua-core`? (Likely separate — keeps kernel pure.)
- How does the misalignment kill-switch interact with `aresume`? (Probably: only human-supplied `aresume` payloads can clear a SWARM-raised interrupt.)
- What's the interface for "agent identity attestation" (MAESTRO layer 3)? Cryptographic? Cached per-process? See `06-open-questions.md`.
