# Core Operational Directives: Deep Dive
**Reference Document for ultrathink-system-skill**

These six directives form the operational backbone of the ultrathink system.
They're always active, regardless of which stage of the methodology you're in.

---

## Directive 1: Plan Node Default 📋

**Principle**: Enter plan mode for ANY non-trivial task (3+ steps). STOP and re-plan if something goes sideways.

### When to Plan
**Always plan for**: 3+ step tasks, architectural decisions, multiple systems, ambiguous requirements, refactoring.
**Skip planning for**: single-step tasks, obvious bug fixes with clear root cause, trivial formatting.

### Minimum Viable Plan
```markdown
# Task: [Name]
## Goal
[1-sentence outcome]
## Steps
1. [Specific action]
2. [Specific action]
3. [Specific action]
## Success Criteria
- [Measurable outcome]
```

### Re-Planning Triggers (STOP immediately)
- Estimate was off by 2x or more
- Discovered a major new requirement
- The approach isn't working
- Tests reveal fundamental design flaw

### Anti-Patterns
❌ "I'll just start coding, the plan will emerge" → Spaghetti code, multiple rewrites
❌ "I already have a mental plan" → Can't collaborate, can't verify approach

### Success Criteria
✅ Plan written down (not in your head)
✅ Plan is specific and checkable
✅ Plan reviewed before execution

---

## Directive 2: Subagent Strategy 🤖

**Principle**: Use subagents liberally to keep main context clean. One task per subagent.

### When to Use Subagents
- Research: "What's the best library for X?"
- Exploration: "Try these 3 approaches and compare"
- Parallel analysis: "Analyze these 5 files for common patterns"
- Deep dives: "Investigate root cause of this bug"
- Proof of concepts: "Can we use X to solve Y?"

### Delegation Patterns

**Pattern 1: Research**
```
Main agent: "I need to choose a caching strategy"
Subagent 1: "Research Redis vs Memcached — performance, persistence, clustering. Return: comparison table."
Subagent 2: "Research CDN caching — distribution, invalidation, cost. Return: comparison table."
Main agent: evaluates both tables, makes informed decision.
```

**Pattern 2: Divide & Conquer**
```
Main agent: "Refactor 10 modules"
Subagent 1: "Refactor modules 1-3"
Subagent 2: "Refactor modules 4-6"
Subagent 3: "Refactor modules 7-10"
Main agent: integrates all changes, runs integration tests.
```

### Subagent Task Template
```markdown
## Subagent Task: [Name]
### Context: [What does the subagent need to know?]
### Task: [Specific action to perform]
### Constraints: [What should/shouldn't they do?]
### Expected Output: [Format of result]
### Success Criteria: [How will we know they succeeded?]
```

### Anti-Patterns
❌ Using subagents for everything (coordination overhead)
❌ Vague subagent tasks (wrong output)
❌ Not providing enough context (wrong assumptions)

### Success Criteria
✅ Main context stays under 70% utilization
✅ Subagents return actionable summaries (not data dumps)
✅ One clear task per subagent

---

## Directive 3: Self-Improvement Loop 🔄

**Principle**: After ANY correction from user, update `tasks/lessons.md`. Ruthlessly iterate until mistake rate drops.

### Always Trigger After
- User corrects your approach
- Tests reveal misunderstanding
- Code review identifies issue
- User says "actually…" or "no, I meant…"

### Lesson Format
```markdown
## YYYY-MM-DD — [Pattern Name]

### What Went Wrong
[Specific description]

### Root Cause
[Why did this happen?]

### Prevention Rule
[How to avoid in future — actionable rule]

### Verification Trigger
[Question to ask yourself before making this mistake]

### Applied To
[Future scenarios this applies to]

### Examples
✅ Good: [What to do]
❌ Bad: [What not to do]
```

### Example Lesson: Premature Optimization
```markdown
## 2026-03-20 — Premature Optimization
### What Went Wrong
Added caching layer before measuring performance.
### Root Cause
Assumed caching would help without profiling first.
### Prevention Rule
NEVER add performance optimizations until:
1. Measured current performance
2. Identified specific bottleneck
3. Estimated improvement potential
### Verification Trigger
"Have I profiled this? What specific metric improves by how much?"
### Examples
✅ Good: "Profiling shows DB queries take 80% of request time. Caching reduces to 10ms."
❌ Bad: "Let's add caching—it might make things faster."
```

### Review Cadence
- **Daily**: Check lessons for current project context
- **Weekly**: Review all lessons, remove duplicates, refine rules
- **Monthly**: Analyze patterns—are certain categories recurring?

### Anti-Patterns
❌ Not writing lessons down (trusting memory)
❌ Vague lessons ("be more careful" ← not actionable)
❌ Write and forget (never reviewing)

### Success Criteria
✅ Lessons file grows over time
✅ Repeat mistakes decline measurably
✅ Rules are specific and actionable

---

## Directive 4: Verification Before Done ✅

**Principle**: NEVER mark a task complete without proving it works programmatically.

### Verification Hierarchy
```
1. Unit Tests       — All new code has tests; all pass locally
2. Integration Tests — Feature works end-to-end; no regressions
3. Manual Testing   — Tested with realistic data and edge cases
4. Self Code Review — Linter passes; no debug artifacts; no TODOs
5. Diff Review      — Compare behavior before vs after
6. Staff Engineer Test — Would a senior approve this?
```

### The Diff Technique
```bash
git checkout main && git pull
./run_tests.sh > before.log
git checkout your-feature-branch
./run_tests.sh > after.log
diff before.log after.log
# New failures = regressions ❌
# New warnings = investigate ⚠️
```

### Programmatic vs Visual
```python
# ❌ Visual: "I see the button is blue"
# (CSS might not have loaded; only blue in dev)

# ✅ Programmatic:
def test_button_color():
    computed = page.find_element("#submit").get_computed_style()
    assert computed["background-color"] == "rgb(0, 0, 255)"
```

### The Staff Engineer Questions
1. Correctness: Does it actually solve the stated problem?
2. Completeness: Are all edge cases handled?
3. Quality: Is the code maintainable?
4. Testing: Are tests meaningful and sufficient?
5. Documentation: Can someone else understand this?
6. Performance: Does it meet requirements?
7. Security: Are there obvious vulnerabilities?

If "no" or "maybe" to any → it's not done.

### Anti-Patterns
❌ Visual-only verification ("Looks good to me!")
❌ Happy-path-only testing
❌ Trusting CI blindly without local runs

### Success Criteria
✅ All tests pass (comprehensive)
✅ Feature works end-to-end realistically
✅ No regressions detected

---

## Directive 5: Demand Elegance (Balanced) ✨

**Principle**: For non-trivial changes, pause and ask "Is there a more elegant way?" Skip for simple/obvious fixes.

### When to Demand Elegance
**Pause for elegance when**:
- Solution feels hacky or fragile
- You're about to add "HACK" or "TODO" comment
- Code will be read/modified frequently
- Affects public API or interface

**Skip elegance when**:
- Fix is obvious and simple
- One-time script or throwaway code
- Urgent hotfix (refactor later)
- Explicit instruction to "just make it work"

### The Elegance Process
```
Step 1: Recognize the hack
Step 2: Ask "Knowing everything now, what's the elegant solution?"
Step 3: Identify the underlying pattern
Step 4: Implement elegantly

Example:
  Before: if type=="A": total += price * 1.1
          if type=="B": total += price * 1.2  # HACK

  Pattern identified: strategy pattern

  After: TAX_RATES = {"A": 1.1, "B": 1.2}
         total = sum(item.price * TAX_RATES.get(item.type, 1.0) for item in items)
```

### Elegance Signals
**Needs elegance**: Hard to explain, copy-paste logic, 5+ parameters, can't find a good name
**Has elegance**: Reads like English, only one way to do it, easy to extend, hard to misuse

### Anti-Patterns
❌ Premature elegance (elegant solution to wrong problem)
❌ Over-abstraction (solving imaginary future problems)
❌ Elegance as excuse ("can't ship until perfect")

---

## Directive 6: Autonomous Bug Fixing 🔧

**Principle**: When given a bug report: just fix it. Zero context switching from user. Investigate, diagnose, fix, verify, report.

### The Autonomous Bug Fix Process
```
Phase 1: Gather Evidence (no user interaction)
  - Check logs (app, error, access)
  - Reproduce the issue
  - Check recent changes (git blame, recent PRs)
  - Run tests (what fails? what does it reveal?)

Phase 2: Diagnose Root Cause
  Symptom → Evidence → Hypothesis → Test hypothesis → Root cause
  No guessing. Follow evidence.

Phase 3: Fix It
  1. Write failing test that reproduces bug
  2. Implement minimal fix
  3. Verify test now passes
  4. Run full test suite (no regressions)
  5. Manual verification in dev environment

Phase 4: Report Back (proactively)
  - What was broken
  - Why it was broken (root cause)
  - What you changed
  - How you confirmed it works
  - How to avoid in future
```

### Failing CI Tests
```bash
# Don't wait for instructions — just fix it:
git fetch && git checkout failing-branch
./run_tests.sh
# Read failures, investigate, fix, verify, push

git commit -m "fix: resolve authentication test failure
Test failing due to incorrect mock setup.
Fixed expected auth token format."
```

### The Zero Context Switching Rule
User says: "Feature X is broken"
You handle: ✅ logs ✅ reproduction ✅ root cause ✅ fix ✅ verification ✅ report
User never needs to: ❌ find error messages ❌ guide debugging ❌ tell you which tests to run

### Anti-Patterns
❌ "Can you send me the error message?" (Look at logs yourself)
❌ "Which test is failing?" (Run tests yourself)
❌ "How should I fix this?" (That's your job to figure out)

---

## Integration: All 6 Directives Together

```
New feature request arrives
        ↓
1. Plan Node Default ── Write tasks/todo.md
        ↓
2. Subagent Strategy ── Offload research/exploration
        ↓
3. Self-Improvement ── Check lessons.md for related patterns
        ↓
4. Demand Elegance ── Pause before committing to design
        ↓
5. Masterful Execution (Stage 4)
        ↓
6. Verification Before Done ── Run verify_before_done.py
        ↓
7. Autonomous Bug Fix ── Fix any failures without asking
        ↓
DONE ✅
```

---

*"These aren't just guidelines — they're the operating system for insanely great work."*
