# Hardware Model Routing — Part 2 Plan
**File:** `2026-04-26-hardware-model-routing-004-PART2-PLAN.md`
**Continues:** `2026-04-26-MERGED-hardware-model-routing-003-PLAN.md`
**Branch:** `main` (commit to `2026-04-24-001-orama-salvage` if re-opened as a branch)
**Status:** G2+G3 closed 2026-04-29 · G1 deferred · G4 blocked (both machines)

---

## Context — What Was Finished in Part 1

| Original Phase | Status | Notes |
|---|---|---|
| Phase 1 — Policy YAML | ✅ Shipped | `config/model_hardware_policy.yml` in PT; `shared:` still empty (intentional, Q3) |
| Phase 2 — discover.py filter | ✅ Shipped | `filter_models_for_platform()` called before every openclaw.json/discovery.json write |
| Phase 3 — AlphaClawManager gate | ✅ Shipped | `validate_routing_affinity()` instance method at line 252 of `alphaclaw_manager.py` |
| Phase 4 — api_server.py API gate | ✅ Shipped | HTTP 400 `HARDWARE_MISMATCH` at line 169; warning log added for stub path |
| Phase 5 — Live config repair | ❌ Not done | Requires both machines online + `discover.py --status` run |
| Phase 6 — Docs / LESSONS | ✅ Shipped | `docs/MODEL_HARDWARE_MATRIX.md`, `docs/LESSONS.md`, `AGENT_RESUME.md` all updated |
| Registry schema (agents[]) | ✅ Fixed | All 7 stage agents now have `"affinity"` keys (commit b2ed93b) |

---

## Open Gap Inventory (4 items)

| # | Gap | File(s) | Status |
|---|-----|---------|--------|
| G1 | `shared:` section in policy YAML is empty | `PT/config/model_hardware_policy.yml` | **DEFERRED** — not needed yet; populate when both machines tested |
| G2 | `PERPETUA_TOOLS_ROOT` not documented in `.env.example` | `orama-system/.env.example`, `PT/.env.example` | ✅ **CLOSED** — already present in both files (line 59 / line 122) |
| G3 | `autoresearch_agents` uses `device_affinity` key; `agents` uses `affinity` | `bin/orama-system/config/agent_registry.json`, `.claude/skills/orama-system/config/agent_registry.json` | ✅ **CLOSED 2026-04-29** — renamed `device_affinity` → `affinity`; values kept as specific GPU IDs (`win-rtx3080`); 7/7 schema tests pass |
| G4 | Live `openclaw.json` has not been repaired on either machine | Runtime file | **BLOCKED** — needs both machines online simultaneously |

### v1.2+ GPU Naming Note
`affinity: "win-rtx3080"` uses the specific GPU identifier, not a generic `"win"` string.
When the RTX 5080 arrives (v1.2+), add a new affinity value `"win-rtx5080"` alongside `"win-rtx3080"`.
Routing code must match on prefix (`win-rtx*`) or exact ID to dispatch to the correct GPU host.
No change needed to existing agents unless they explicitly target the new GPU.

---

## Phase 5 — Live Config Repair (Blocked: Both Machines Required)

**Prerequisite:** Mac and Windows both online with LM Studio running.

### Step 5.1 — Backup existing configs (both machines)

```bash
# Mac
cp ~/.openclaw/openclaw.json ~/.openclaw/openclaw.json.bak-$(date +%Y%m%d)
cp discovery.json discovery.json.bak-$(date +%Y%m%d) 2>/dev/null || true

# Windows (run in orama-system dir)
copy openclaw.json openclaw.json.bak
```

### Step 5.2 — Re-run discover.py with policy enforcement active

```bash
# Set env var first
export PERPETUA_TOOLS_ROOT=/path/to/perplexity-api/Perpetua-Tools

# Run discovery — this triggers filter_models_for_platform() before every write
python scripts/discover.py --all

# Verify: mac-only models absent from Windows output, windows-only absent from Mac
python scripts/hardware_policy_cli.py validate
```

### Step 5.3 — Populate `shared:` section in policy YAML

After running discovery on both machines, compare model lists:

```bash
# On Mac:
python scripts/discover.py --status | grep "model:" > /tmp/mac_models.txt

# On Windows:
python scripts/discover.py --status | grep "model:" > /tmp/win_models.txt

# Diff to find models present on BOTH:
comm -12 <(sort /tmp/mac_models.txt) <(sort /tmp/win_models.txt)
```

Add confirmed cross-platform models to `PT/config/model_hardware_policy.yml`:

```yaml
shared:
  - llama3.2:3b          # example — verify before adding
  - phi3.5:mini          # example — verify before adding
```

Closes **G1**.

---

## Phase 7 — Schema Normalization: `device_affinity` → `affinity`

The `autoresearch_agents` block uses `device_affinity` (string, e.g. `"win-rtx3080"`, `"mac"`).
The `agents` array uses `affinity` (string, e.g. `"win"`, `"mac"`).

### Step 7.1 — Decide canonical key name

Recommendation: adopt `affinity` everywhere. `device_affinity` was the original key before
the hardware policy work unified naming.

### Step 7.2 — ✅ DONE (2026-04-29) — Migrated `autoresearch_agents` entries

Renamed `device_affinity` → `affinity` in both:
- `bin/orama-system/config/agent_registry.json`
- `.claude/skills/orama-system/config/agent_registry.json`

**Decision: specific GPU IDs kept** (NOT normalized to `"win"`):

| Key change | Value decision |
|-----------|-----------|
| `device_affinity` → `affinity` | `"win-rtx3080"` — kept specific (RTX 5080 adds `"win-rtx5080"` in v1.2+) |
| `device_affinity` → `affinity` | `"mac"` — unchanged |

Routing code reading `affinity` must match on exact GPU ID or `win-rtx*` prefix.

### Step 7.3 — ✅ DONE — routing code verified clean

`grep -r "device_affinity"` → zero results in all `.py`/`.json` files.

### Step 7.4 — ✅ DONE — 7/7 schema tests pass

```
python3 -m pytest scripts/tests/test_agent_registry_schema.py -v  → 7 passed
```

Closes **G3**.

---

## Phase 8 — ✅ CLOSED (G2 already done)

`PERPETUA_TOOLS_ROOT` was already present in both `.env.example` files before this session:
- `orama-system/.env.example` line 59
- `PT/.env.example` line 122

No action needed. Closes **G2**.

---

## Verification Checklist

- [x] `grep -r "device_affinity" . --include="*.py" --include="*.json"` → zero results (G3 closed 2026-04-29)
- [x] `python3 -m pytest scripts/tests/test_agent_registry_schema.py -v` → 7/7 passed (G3 closed)
- [x] `cat .env.example | grep PERPETUA_TOOLS_ROOT` → entry present (G2 already closed)
- [ ] `python -m pytest scripts/tests/ -q` → full suite pass in orama-system (pending)
- [ ] `python -m pytest tests/ -q` → full suite pass in Perpetua-Tools (pending)
- [ ] `cat config/model_hardware_policy.yml | grep -A5 "shared:"` → at least 1 entry (G1 — DEFERRED)
- [ ] `openclaw.json` on both machines repaired (G4 — BLOCKED: both machines required)

---

## Remaining Work (Part 3 scope)

| Item | When |
|------|------|
| G4 — live openclaw.json repair | Both machines online |
| G1 — populate `shared:` models section | Both machines online + G4 done |
| v1.2+ — add `win-rtx5080` affinity + routing | When RTX 5080 machine is provisioned |
| Full test suite pass (orama + PT) | Next available session |

---

## Lessons Recorded (2026-04-29)

- Specific GPU ID in `affinity` (`win-rtx3080`) is correct — do NOT normalize to generic `"win"`
- RTX 5080 will add `affinity: "win-rtx5080"` as a new value; routing code must handle both IDs
- `device_affinity` key is now fully retired in all JSON files; `affinity` is canonical
- G2 was already done before this session — always check before implementing "pending" tasks
