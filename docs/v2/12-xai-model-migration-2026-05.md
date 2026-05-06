# 12 — xAI Model Retirement & Migration (Effective 2026-05-15)

> **Status**: Active | Added 2026-05-06
> **Scope**: `perpetua-core/config/model_hardware_policy.yml` + `oramasys/` routing +
> any non-kernel module that dispatches to the xAI (`grok-*`) API endpoint.
> **Deadline**: 2026-05-15 12:00 PM PT — requests to retired models stop working.

---

## 1. Retired models

Effective **2026-05-15 12:00 PM PT**, the following model IDs will no longer
accept API requests from the xAI endpoint:

| Model ID | Workload type |
|----------|--------------|
| `grok-4-1-fast-reasoning` | reasoning |
| `grok-4-1-fast-non-reasoning` | non-reasoning |
| `grok-4-fast-reasoning` | reasoning |
| `grok-4-fast-non-reasoning` | non-reasoning |
| `grok-4-0709` | general |
| `grok-code-fast-1` | coding |
| `grok-3` | general |
| `grok-imagine-image-pro` | image generation |

After the deadline, any `model_hardware_policy.yml` entry or router constant
that still references these IDs will cause a hard dispatch failure at the
`HardwarePolicyResolver` gate. **All references must be migrated before
2026-05-15.**

---

## 2. Replacement routing (v2 defaults)

### 2a. Reasoning workloads → `grok-4.3`

```yaml
# perpetua-core/config/model_hardware_policy.yml
- model: grok-4.3
  provider: xai
  hardware_tier: shared          # API model — no local VRAM constraint
  task_types: [coding, reasoning]
  role: coding_fallback_default
  notes: >
    Coding fallback default (medium effort mode).
    ACT mode (real code writes) suspended until Win-coder slot is available.
    Until then: PLAN-ONLY for coding tasks — emit plan, do not write files.
```

**Behaviour until Win-coder is available:**
- `task_type: coding` dispatches to `grok-4.3` in **plan-only mode**
  (generate plan + diffs; do not execute file writes).
- Real `ACT` (file mutations) resumes automatically once the Win-coder
  hardware slot is confirmed available in `swarm_state.md`.
- Non-coding reasoning tasks (`task_type: reasoning`) route to `grok-4.3`
  with full ACT enabled.

### 2b. Non-reasoning workloads → `grok-4.20-non-reasoning`

```yaml
- model: grok-4.20-non-reasoning
  provider: xai
  hardware_tier: shared
  task_types: [research, ops, summarisation, chat]
  role: non_coding_default
  notes: >
    All non-coding tasks go here by default.
    Replaces grok-4-1-fast-non-reasoning, grok-4-fast-non-reasoning, grok-3.
```

### 2c. Image generation

`grok-imagine-image-pro` has no announced replacement at time of writing.
Remove the image-generation route from `model_hardware_policy.yml` and log
a warning if a task_type of `image` is dispatched — do not silently fall
back to a text model.

---

## 3. Migration checklist (pre-2026-05-15)

- [ ] `perpetua-core/config/model_hardware_policy.yml` — remove all 8 retired
      IDs; add `grok-4.3` (reasoning/coding) and `grok-4.20-non-reasoning`
      (non-coding).
- [ ] `perpetua-core/config/model_hardware_policy.example.yml` — same.
- [ ] `oramasys/` router constants / dispatch logic — grep for retired IDs,
      replace with new defaults.
- [ ] `config/hardware_policy_cache.yml` (this repo's DR fallback) — if any
      retired grok IDs appear, remove them. *(Currently none — cache only
      tracks local LM Studio / Ollama models.)*
- [ ] `docs/LESSONS.md` — entry logged (2026-05-06).
- [ ] CI: add `test_no_retired_model_ids` — grep `model_hardware_policy.yml`
      for any retired ID and fail if found.

---

## 4. Routing summary table (post-migration)

| Task type | Default model | Mode | Condition |
|-----------|--------------|------|-----------|
| `coding` | `grok-4.3` | **PLAN-ONLY** | until Win-coder slot confirmed |
| `coding` | `grok-4.3` | **ACT** | after Win-coder available |
| `reasoning` | `grok-4.3` | ACT | always |
| `research` | `grok-4.20-non-reasoning` | ACT | always |
| `ops` | `grok-4.20-non-reasoning` | ACT | always |
| `chat` / `summarisation` | `grok-4.20-non-reasoning` | ACT | always |
| `image` | *(no replacement)* | ERROR | log + surface to user |

---

## 5. Win-coder availability gate

The coding ACT resume is gated on `swarm_state.md` reporting
`WIN_CODER: AVAILABLE`. Until that flag is set:

```python
# perpetua_core/policy/dispatch.py (sketch)
if task.task_type == "coding" and not hw_resolver.win_coder_available():
    raise PlanOnlyModeError(
        "Coding ACT suspended: Win-coder slot unavailable. "
        "Plan emitted — re-submit to execute when Win-coder is ready."
    )
```

`win_coder_available()` reads `swarm_state.md` (same file already checked by
the Windows-sequential-load rule in `CLAUDE.md §4`). No new state source
introduced.

---

## 6. Cross-references

- `docs/LESSONS.md` (2026-05-06 entry) — retirement notice + routing decision
- `docs/v2/07-agate-vision.md` — `model_hardware_policy.yml` as open standard;
  this migration is an example of the "new model → add a row" update cycle
- `docs/v2/11-idempotency-and-guard-patterns.md` §3 — Pattern B: all model ID
  lists must be single-source in `perpetua-core/config/`; never duplicated
  across bash + python
- `CLAUDE.md §4` — Windows GPU sequential load rule + `swarm_state.md` gate
