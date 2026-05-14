# 04 — Build Order (GPT Phase 1–4 + lift-from-v1 mapping)

> Implements D9. Sequence: primitives → graph engine → HTTP surface → parity tests.
> Lift battle-tested code from today's `orama-system` where it fits.

---

## Prerequisite gate

**v1.0 RC shipped** (D3). The 5-task `2026-04-28-perpetua-orama-master-revamp.md` plan closed.
v1 is at 0.9.9.8. **Gate cleared.**

---

## Phase 0 — Repository Initialization ✅ DONE (2026-05-02)

The 3 new repositories (\`agate\`, \`oramasys\`, \`perpetua-core\`) have been initialized at \`/Users/lawrencecyremelgarejo/Documents/oramasys/\`. Initial code for state, LLM client, policy, and the MiniGraph engine has been committed.

---

## Phase 1 — Primitives Hardening (\`perpetua-core\`) ✅ DONE (2026-05-01)

**Shipped:** \`oramasys/perpetua-core\` commit \`2f717f5\` — async \`GossipBus\` (aiosqlite), all 6 \`graph/plugins/\` implemented, 32 tests passing (Python 3.11+).
See \`15-phase1-as-built.md\` for full module table and OQ resolutions.

## Phase 2 — Engine & Safety Integration (\`perpetua-core/graph/\`) — PARTIALLY DONE

**Done (shipped in 2f717f5):**
- \`GraphPlugin\` protocol: all 6 plugins in \`graph/plugins/\`
- Conditional edges (callable in \`add_edge\`)
- HITL interrupts (duck-typed \`Interrupt\` exception)
- Streaming (plugin)
- Subgraphs (plugin)
- \`@tool\` decorator (plugin)

**Still needed (Phase 2 next work):**
- \`max_steps\` safety guard in \`ainvoke\` (OQ12 — prevents infinite loops)
- Sentinel Node for SWARM misalignment monitoring
- \`perpetua_core/message.py\` typed Message wrapper (OQ17 — before Phase 3 LLMClient wiring)

## Phase 3 — Orchestration & API Layer (\`oramasys/\`) ← NEXT

- **Verify**: API Server properly consumes PT affinity signals.
- **Wire**: LLMClient to \`dispatch_node\`.

## Phase 4 — Parity tests ← NEXT

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

### Phase 4 additional CI gates (from `11-idempotency-and-guard-patterns.md`)

These gates are mandatory before Phase 4 is considered complete:

| Gate | File | What it catches |
|------|------|-----------------|
| `test_ensure_symlink_all_four_states_idempotent` | per-plugin in `perpetua-core/graph/plugins/tests/` | fs helper crashes under `set -e`; broken-symlink, regular-file, stale-target branches |
| `test_validators_agree_on_identity_set` | `perpetua-core/tests/test_policy_parity.py` | bash/python allowlist drift — silent commit failures |
| `test_validators_agree_on_hardware_tiers` | same | hardware-tier allowlist drift across bash and python |
| `test_*_works_from_unrelated_cwd` | `oramasys/tests/test_start_sh.py` | symlinks landing in caller's CWD instead of `$SCRIPT_DIR` |
| **Multi-agent review pass** | CI pipeline step | run Codex or Gemini over kernel diff before merge; log new findings to LESSONS.md |

See `11-idempotency-and-guard-patterns.md` §§2–4 for reference implementations and §6 for the 3-pass review pipeline design.

### Phase 4 mandatory accountability CI gates

The following gates must be green before parity is declared and v2.0 is released. They verify the five-rule Human Accountability Framework is structurally enforced — not just documented (see `03-safety-v2.5.md` §Human Accountability Framework):

| Gate | Test | Rule enforced |
|------|------|---------------|
| Interrupt not suppressible by node | `test_interrupts.py::test_interrupt_not_suppressible_by_node` | R3 — always-escapable |
| Conflicted status is terminal-until-human | `test_interrupts.py::test_conflicted_state_requires_aresume` | R5 — escalation to humans |
| GossipBus is append-only | `test_gossip.py::test_no_delete_or_update` | R4 — transparent audit log |
| Authorization event precedes subprocess | `test_tool_node.py::test_authorization_event_precedes_subprocess` | R2 — human authorization |
| `aresume` records `authorized_by` in state | `test_interrupts.py::test_aresume_writes_authorized_by` | R2 — accountability chain |

These five tests are CI-blocking. A parity run with any of these failing does not count as Phase 4 complete.

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
