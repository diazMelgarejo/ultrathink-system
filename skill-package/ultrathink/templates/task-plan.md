# Task: [Task Name Here]
**Date**: YYYY-MM-DD
**Optimize for**: reliability | creativity | speed
**Status**: 🔄 In Progress | ✅ Done | ⏸ Blocked

---

## Goal
[What does success look like? 1-2 sentences maximum.]

---

## Constraints
- Technical: [e.g., must use existing auth system, latency < 200ms]
- Business: [e.g., demo needed by Friday, can't break existing API]
- Compliance: [e.g., no PII in logs, GDPR applies]

## Non-Goals
- [Explicitly list what we are NOT doing in this task]
- [Scope creep prevention — be specific]

---

## ✓ Plan First

> Review and check off before starting implementation.

### Phase 1: Context (Stage 1)
- [ ] Scan project structure and git history
- [ ] Review CLAUDE.md / AGENTS.md / SKILL.md
- [ ] Identify existing patterns and naming conventions
- [ ] List constraints that will shape the solution

### Phase 2: Architecture (Stage 2)
- [ ] Design module breakdown (what are the components?)
- [ ] Define interfaces between components
- [ ] Identify edge cases upfront
- [ ] Check: does this compose with existing skills?

### Phase 3: Refinement (Stage 3)
- [ ] Apply quality rubric (simplicity, readability, robustness)
- [ ] Ask: "Is there a more elegant way?"
- [ ] Confirm: removing any piece would break functionality

### Phase 4: Implementation (Stage 4)
- [ ] Step 1: [Replace with specific first step]
- [ ] Step 2: [Replace with specific second step]
- [ ] Step 3: [Replace with specific third step]
- [ ] Step 4: Write tests (TDD preferred — tests before/alongside code)
- [ ] Step 5: Integration test end-to-end
- [ ] Step 6: Edge cases and error handling

### Phase 5: Verification (Directive #4)
- [ ] `python scripts/verify_before_done.py --task "[Task Name]"`
- [ ] All tests pass (no failures, no skips)
- [ ] No debug artifacts (no print/console.log/TODO)
- [ ] Linting passes
- [ ] Staff engineer self-review: would I approve this?

---

## ✓ Verify Plan

> [ ] Reviewed with user/team on: ___________
> Notes: ___________

---

## ✓ Track Progress

Mark items above `[x]` as you complete them.

**Progress log** (append entries as you work):
```
YYYY-MM-DD HH:MM — [What was completed / decision made]
```

---

## ✓ Document Results

> Complete this section when done.

### What Was Built
[Brief description of what was implemented — 2-4 sentences]

### Key Decisions
| Decision | Chosen | Alternatives Considered | Reason |
|----------|--------|------------------------|--------|
| [e.g., DB] | PostgreSQL | MongoDB, SQLite | ACID guarantees needed |

### Test Results
```
Unit tests:        ___ passing, ___ failing
Integration tests: ___ passing, ___ failing
Coverage:          ___%
```

### Performance
[Any benchmarks or metrics — or "not measured / not applicable"]

---

## ✓ Capture Lessons

> Run `python scripts/capture_lesson.py` if any corrections were needed.

Lessons captured this task:
- [ ] None needed
- [ ] [Pattern name] — see tasks/lessons.md

---

## Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| [Risk 1] | Low/Med/High | Low/Med/High | [Mitigation strategy] |

---

*Template: ultrathink-system v0.9.9.0 | Directive #1: Plan Node Default*
