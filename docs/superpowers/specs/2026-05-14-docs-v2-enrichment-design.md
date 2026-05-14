# docs/v2 Enrichment — Canonical As-Built + OQ Resolution Design

**Date:** 2026-05-14
**Author:** brainstorming session (Claude + Lawrence)
**Status:** Approved → executed same session

---

## Problem

The `diazMelgarejo/orama-system/docs/v2/` spec tree was reverted to commit `935ce54` after a session where Claude accidentally documented a divergent (non-canonical) build as Phase 1. The reverted docs are ALREADY largely correct — the README, D8 revision note, and module roadmap were all accurate. Only targeted additions are needed.

---

## Canonical ground truth

| Repo | Commit | Date | Tests | Key facts |
|------|--------|------|-------|-----------|
| `oramasys/perpetua-core` | `2f717f5` | 2026-05-01 | 32 ✅ | 65-line engine + 6 plugins, BaseModel, aiosqlite, Python 3.11+ |
| `oramasys/oramasys` | `d123420` | 2026-05-01 | 4 ✅ | FastAPI /run + /health, placeholder dispatch_node |
| `oramasys/agate` | `755e1de`/`f1d5a57` | 2026-05-01 | — | Hardware policy JSON Schema + GGUF RFC, spec-only |

**Hard constraint:** All doc changes go to `diazMelgarejo/orama-system/docs/v2/` ONLY. Do NOT push to `oramasys/*`.

---

## Approach chosen

**Approach A — Full docs refresh, preserve original planning docs as much as possible.** Minimal edits to 4 existing files + 1 new file. No restructuring. No deletion of original spec content.

Rationale: "Preserve original plans and limit attack surface of potential damage due to lack of context."

---

## File map

| File | Action | What changes |
|------|--------|-------------|
| `docs/v2/15-phase1-as-built.md` | **CREATE** | Full 3-repo canonical as-built with module tables + OQ resolution table |
| `docs/v2/06-open-questions.md` | **EDIT** | Remove OQ4/7/8 from Active; update OQ11 in Resolved; add OQ4/7/8/(OQ13)/(OQ14)/(OQ16) to Resolved; fix D8 row |
| `docs/v2/04-build-order.md` | **EDIT** | Phase 1 → DONE (2026-05-01); Phase 2 → PARTIALLY DONE; update next steps |
| `docs/v2/00-context-and-decisions.md` | **EDIT** | One implementation note appended to D8 section |
| `docs/v2/README.md` | **EDIT** | Add `oramasys/agate/` to repo topology; add docs 14 and 15 to spec tree |

---

## What was NOT changed

- `01-kernel-spec.md` — already correct
- `03-safety-v2.5.md` — not affected
- All `02-modules/` files — not affected
- `05-feasibility-review.md` through `14-supervisor-and-anthropic-patterns.md` — not affected
- Nothing in `/Users/lawrencecyremelgarejo/Documents/oramasys/` (manual review required first)

---

## Post-execution state

After this enrichment:
- `docs/v2/15-phase1-as-built.md` is the authoritative record of what v2.0-alpha.1 shipped
- `docs/wiki/10-wrong-repo-build-what-not-to-do.md` is the cautionary artifact of what NOT to do
- `docs/LESSONS.md` has the full post-mortem
- All OQs resolved by the canonical build are recorded in `06-open-questions.md`
- Build order reflects Phase 1 complete, Phase 2 partial

---

## Next session gates (user-led, before any Phase 2 code)

1. Run `python -m pytest tests/ -v` in both `perpetua-core` (expect 32) and `oramasys` (expect 4)
2. Read all 6 plugin files in `perpetua_core/graph/plugins/`
3. Verify all 3 repos are 0 ahead/0 behind remote
4. Only after manual review passes: open a NEW brainstorm session for Phase 2 code planning
