# Pre-Completion Verification Checklist
**ultrathink System — Directive #4: Verification Before Done**

> Run this checklist before marking ANY task complete.
> Or use: `python scripts/verify_before_done.py --task "Task Name"`

---

## Task: ___________________________
**Date**: ___________  **Branch**: ___________

---

## 1. Unit Tests ✓

- [ ] All new code has corresponding tests
- [ ] All tests pass locally (`pytest` / `npm test`)
- [ ] Happy path tested
- [ ] Edge cases tested (empty input, null, max values, boundary conditions)
- [ ] Error conditions tested (invalid input, network failure, timeout)
- [ ] No tests are skipped or commented out

**Coverage**: ___%  **Target**: > 80%

---

## 2. Integration Tests ✓

- [ ] Feature works end-to-end in dev environment
- [ ] Integrates correctly with existing systems
- [ ] No regressions in related features
- [ ] Database migrations work cleanly (if applicable)
- [ ] External API calls handle failure modes

---

## 3. Manual Testing ✓

- [ ] Tested with realistic data (not just "test" / "foo" values)
- [ ] Tested edge cases manually
- [ ] Tested error scenarios manually
- [ ] UI works correctly (if applicable)
- [ ] Tested on target environments/platforms

---

## 4. Code Quality ✓

- [ ] Linter passes with zero errors (`flake8` / `eslint`)
- [ ] Type checker passes (if applicable: `mypy` / `tsc`)
- [ ] No `print()` or `console.log()` debug statements
- [ ] No commented-out code blocks
- [ ] No `TODO` or `FIXME` without a linked ticket
- [ ] No `HACK` comments (refactor first)
- [ ] No hardcoded secrets, passwords, or API keys

---

## 5. Diff Review ✓

- [ ] Reviewed `git diff main` line by line
- [ ] No unintended file changes included
- [ ] No performance degradation
- [ ] No new errors in application logs
- [ ] Behavior change is intentional and expected

---

## 6. Documentation ✓

- [ ] Public APIs have docstrings
- [ ] Complex logic has comments explaining "why" (not "what")
- [ ] README updated if needed
- [ ] CHANGELOG.md updated (if user-facing change)
- [ ] Migration guide written (if breaking change)
- [ ] ADR created (if significant architectural decision)

---

## 7. Security ✓

- [ ] No hardcoded credentials
- [ ] Input validation present for all user-controlled data
- [ ] Error messages don't leak sensitive information
- [ ] SQL queries use parameterization (no string concatenation)
- [ ] File operations validate paths (no path traversal)

---

## 8. Staff Engineer Test ✓

Answer honestly. If "no" or "unsure" — keep refining.

- [ ] **Correctness**: Does it actually solve the stated problem?
- [ ] **Completeness**: Are all edge cases handled?
- [ ] **Quality**: Is the code maintainable and readable?
- [ ] **Testing**: Are tests meaningful and comprehensive?
- [ ] **Documentation**: Can someone else understand this in 6 months?
- [ ] **Performance**: Does it meet requirements?
- [ ] **Security**: Are there obvious vulnerabilities?
- [ ] **Pride**: Am I proud to put my name on this?

---

## Final Sign-Off

- [ ] `python scripts/verify_before_done.py --task "[Task Name]"` ran and PASSED
- [ ] All checkboxes above checked
- [ ] Task marked complete in `tasks/todo.md`
- [ ] Lessons captured in `tasks/lessons.md` (if corrections were needed)

**Verified by**: ___________  **Date**: ___________

---

*Template: ultrathink-system v1.0.0 | Never trust visual alone. Always verify programmatically.*
