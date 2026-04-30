# 04 — Build Order (GPT Phase 1–4 + lift-from-v1 mapping)

> Implements D9. Sequence: primitives → graph engine → HTTP surface → parity tests.
> Lift battle-tested code from today's `orama-system` where it fits.

---

## Prerequisite gate

**v1.0 RC must ship first** (D3). The 5-task `2026-04-28-perpetua-orama-master-revamp.md`
plan must close before Phase 1 begins. As of 2026-04-30, Tasks 2–4 are landed (per
`9f797b0` and `dec4a61` commits). Remaining v1.0 RC work continues until tag.

---

## Phase 1 — Primitives (`perpetua-core/perpetua_core/`)

Implements: `state.py`, `message.py`, `llm.py`, `policy.py`, `gossip.py`.

Lift from v1:
- `HardwareAffinityError` exception class — already canonicalized in v1's `2026-04-28` revamp Task 4. **Direct copy** with namespace re-anchored.
- `model_hardware_policy.yml` schema — lift schema shape; rebuild content per D8 example.
- LM Studio LAN routing config — port `routing.json` (Mac `.110:1234`, Windows `.108:1234`) into `model_hardware_policy.example.yml`.

Acceptance: `pytest perpetua-core/tests/test_state.py test_policy.py test_llm.py test_gossip.py` all green.

## Phase 2 — Graph engine (`perpetua-core/perpetua_core/graph/`)

Implements: `engine.py`, `nodes.py`, `edges.py`, `checkpointer.py`, `interrupts.py`,
`subgraphs.py`, `tool.py`, `streaming.py`. Tier 3 features per D8.

No lift from v1 — graph engine is genuinely new (v1 has no MiniGraph equivalent;
ultrathink's 5-stage flow is hardcoded in `bin/agents/orchestrator/`).

Acceptance: all `tests/test_*.py` for graph submodules green; line count audit
shows kernel total ≤ 250 lines (Tier 3 budget + 15% slack).

## Phase 3 — HTTP surface (`oramasys/`)

Implements: `oramasys/api/server.py`, `oramasys/api/contracts.py`, `oramasys/graphs/perpetua_graph.py`.

Lift from v1:
- `api_server.py` skeleton — extract FastAPI app pattern + middleware + error handlers. **Recycle the husk** (Grok). Replace internals to invoke `oramasys` graph instead of v1's hardcoded ultrathink pipeline.
- Pydantic v2 request/response shapes from `bin/orama-system/references/api_contract.md`.

Acceptance: `uvicorn oramasys.api.server:app` boots; `POST /run` round-trips a 3-node graph and returns valid `RunResponse`. Handlers ≤ 10 lines (lint).

## Phase 4 — Parity tests

Build a v2.0 `oramasys` graph that reproduces v1's ultrathink 5-stage flow
(Context → Architecture → Refinement → Execution → Crystallization → Output)
end-to-end. Tests assert outputs match v1 within tolerance.

This validates that we haven't regressed capability. Once parity is verified,
v1.0 RC can be marked superseded for the kernel + glass-window scope (non-kernel
modules continue to be carried forward separately).

Acceptance:
- `pytest oramasys/tests/test_parity.py` green against fixtures captured from
  v1.0 RC runs.
- LM Studio LAN integration: same prompt routed through v2.0 graph hits the same
  Mac vs Windows endpoints as v1 routes it (per `model_hardware_policy.yml`).

---

## Summary of lift-from-v1 inventory

| v1 source | Where it lifts into v2 | Treatment |
|-----------|------------------------|-----------|
| `HardwareAffinityError` class | `perpetua_core/policy.py` | Direct copy, namespace re-anchored |
| `model_hardware_policy.yml` schema | `perpetua_core/config/model_hardware_policy.example.yml` | Schema lifted, content rebuilt per D8 |
| `routing.json` LM Studio endpoints | example yaml | Mac `.110:1234`, Windows `.108:1234` carried |
| `api_server.py` FastAPI skeleton | `oramasys/api/server.py` | Husk recycled, internals replaced |
| API request/response Pydantic shapes | `oramasys/api/contracts.py` | Shapes lifted, retyped for Pydantic v2 |
| `bin/orama-system/references/api_contract.md` | reference for above | docs lift |

**Not lifted** (rebuilt fresh): everything else. ultrathink pipeline, agent registry,
MCP server stubs, network autoconfig, lessons system — all reconsidered as
non-kernel modules under `02-modules/`.
