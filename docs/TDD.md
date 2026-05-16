# TDD — Test-Driven Development Checklists

> **Canonical path**: `orama-system/docs/TDD.md`
> **Companion**: parent-dir [`tdd.md`](../../tdd.md) — source-of-truth philosophy (SPECS → tests → code).
> **External skill**: [`superpowers:test-driven-development`](file://~/.claude/plugins/cache/claude-plugins-official/superpowers/5.0.7/skills/test-driven-development/SKILL.md) — full methodology, anti-patterns. Do not duplicate here.
> **Anti-patterns reference**: same dir, `testing-anti-patterns.md`.

This file is the **prescriptive gate**. Two short checklists. Use them before every code change and every commit.

---

## Pre-Code-Change Checklist

Before writing or modifying production code:

1. **Did I write a failing test first?**
   - YES → run it, confirm it fails for the right reason, then write code.
   - NO → STOP. Either write the test, OR document the reason for skipping in the commit message (one line: `tdd-skip: <reason>`). Acceptable skip reasons: pure refactor with no behavior change; doc-only change; experimental spike marked `WIP`. Everything else needs a test.

2. **Is the failing test the smallest one that would catch the bug if it regressed?**
   - One assertion if possible. One file boundary crossed at most.

3. **Does the test name describe the behavior, not the implementation?**
   - Good: `falls back to default model when env var is empty string`.
   - Bad: `test_command_center_line_33`.

---

## Pre-Commit Checklist

Before `git commit`:

1. **Did the test actually fail before the fix and pass after?** Re-run with the fix reverted if uncertain. A test that never failed is not a TDD test — it is theater.
2. **Did I run the full local suite?** `npm test` / `pytest` — green before commit.
3. **For Vite frontend changes:** did I add or extend a `*.test.ts` / `*.test.tsx` next to the changed file? (See gap section below.)
4. **For SQL / migrations:** did I include an idempotency test (run twice, second run is a no-op)?
5. **Commit message names the test file** if a non-trivial test was added. Reviewers should not have to grep for it.

---

## Vite Frontend Gap (RC-1 Code Review Finding)

As of the RC-1 review, the Vite frontend has **zero `*.test.ts*` files in `src/`**. This is the single largest TDD gap in the repo.

### Minimum acceptance gate before any production rollout

- **Toolchain installed and wired:** Vitest + React Testing Library + `@testing-library/jest-dom`. `vitest` script in `package.json`. CI runs it.
- **At least one test per top-level page/route component**, covering the happy-path render and one branch in any conditional logic.
- **Every fallback / default-value branch is tested.** The RC-1 review surfaced two such branches that would have been caught:
  - `src/components/CommandCenter.tsx:33` — fallback logic on missing/empty model id; test must cover empty string AND undefined.
  - `src/lib/client.ts:26` — dead ternary branch; a test asserting both sides forces the dead branch to be removed or justified.
- **No PR merged to main that touches `src/` without at least one accompanying test**, unless `tdd-skip:` reason is documented and approved.

### Recommended first tests to write (in order)

1. `CommandCenter.test.tsx` — covers the `:33` fallback (both branches).
2. `client.test.ts` — covers the `:26` ternary (forces decision: keep both branches with assertions, or delete the dead one).
3. One smoke test per top-level route component (renders without crashing).

These three unblock the gate. Everything else is incremental.

---

## Canonical "Would-Have-Been-Caught-By-TDD" Examples

When teaching this workflow or reviewing a PR that skipped tests, point at these two RC-1 bugs:

| Bug | Why TDD would have caught it |
|-----|------------------------------|
| `CommandCenter.tsx:33` — fallback path silently swallowed an empty-string model id and used the wrong default | A test feeding `""` and asserting the resolved default would have failed before the bug shipped. |
| `client.ts:26` — ternary with an unreachable branch (dead code) | Writing the test for both sides of the ternary forces the author to either reach the dead branch (proving it isn't dead) or delete it. Either outcome is a win. |

If a PR is proposed that looks structurally similar to either of these (a fallback on falsy input, or a ternary on a value the author claims is "always defined"), reviewers should require a test before approving.

---

## Escape Hatches (use sparingly)

- **Pure refactor, no behavior change:** allowed without a new test if existing tests cover the refactored surface and stay green. If they don't, add coverage first, then refactor.
- **Exploratory spike:** allowed on a branch marked `spike/*`. Spike branches never merge to main as-is — they get rewritten with tests on a `feat/*` branch.
- **Doc-only / config-only changes:** no test required.

Anything else: write the test.

---

## References

- Parent philosophy doc: [`../../tdd.md`](../../tdd.md)
- Full TDD methodology + anti-patterns: `~/.claude/plugins/cache/claude-plugins-official/superpowers/5.0.7/skills/test-driven-development/`
- Session lessons: [`LESSONS.md`](LESSONS.md)
- Verifier gate (crystallization blocked without approved test result): [`2026-05-14--UNIFIED-ABSORPTION-PLAN.md`](2026-05-14--UNIFIED-ABSORPTION-PLAN.md) § 2
