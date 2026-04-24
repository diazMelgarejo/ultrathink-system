# ultrathink 5-Stage Methodology: Deep Dive

## Reference Document for orama-system

---

## Philosophy: Technology + Humanity

Technology alone is not enough. It's technology married with the liberal arts,
married with the humanities, that yields results that make our hearts sing.

Your work should:

- Integrate seamlessly into human workflows
- Feel intuitive and purposeful, never mechanical
- Solve the *real* problem, not just the stated one
- Leave the codebase, product, and team wiser than you found them

When something seems impossible, that's your cue to **ultrathink harder.**

---

## The Feedback Loop

The 5 stages are not strictly sequential — they form a feedback loop:

```
Context Immersion ←─────────────┐
        ↓                       │
Visionary Architecture          │
        ↓                       │
Ruthless Refinement             │
        ↓                       │
Masterful Execution             │
        ↓                       │
Crystallize Vision ─────────────┘
        ↓
    [DONE]
```

### Loop back when

- Context → Architecture: Discovered new constraints
- Architecture → Refinement: Design is too complex
- Refinement → Architecture: Simplification revealed better approach
- Execution → Any stage: Tests revealed flawed assumptions

---

## Stage 1: Context Immersion (Progressive Deepening)

### What It Means

Ground yourself deeply in the problem space before proposing solutions.
Don't reach for the first working answer — understand the entire landscape.

### Information Sources (Priority Order)

1. **Git history** — Commit messages, PR descriptions, resolved issues
2. **Documentation** — CLAUDE.md, AGENTS.md, SKILL.md, README files
3. **Architecture** — Design docs, ADRs, system diagrams
4. **Code patterns** — Idioms, naming conventions, error handling styles
5. **Constraints** — Tech debt, performance requirements, compliance needs

### Diagnostic Questions

- What problem is this system *really* solving?
- What are the non-negotiable constraints?
- What patterns does the codebase already follow?
- What have previous solutions taught us?
- What assumptions might be invisible to me right now?

### Output Format

```markdown
## Context Summary

### System Purpose
[2-3 sentences on what this system does and why]

### Key Constraints
- Technical: [latency < 100ms, memory < 512MB]
- Business: [must support 10k concurrent users]
- Compliance: [GDPR, SOC2, HIPAA]

### Existing Patterns
- Architecture: [microservices with event sourcing]
- Language idioms: [dependency injection, error-as-values]
- Testing: [TDD, property-based testing]

### Historical Lessons
- What worked: [async processing reduced latency 80%]
- What didn't: [caching layer added complexity, no benefit]
- Pain points: [deployment takes 2 hours]
```

### Common Mistakes

- ❌ Skipping this stage to "save time" (always costs more later)
- ❌ Assuming your experience applies without verifying
- ❌ Ignoring git history ("old code doesn't matter")
- ❌ Not identifying constraints until after building

### Success Criteria

- Can explain system to a new team member in 5 minutes
- Can predict how existing code will react to proposed changes
- Have identified 3+ constraints that will shape the solution
- Understand why previous solutions succeeded or failed

---

## Stage 2: Visionary Architecture (Think Different + Decomposition)

### What It Means

Break the problem into modular sub-problems and envision the most elegant
solution possible. Think like a designer: what would the ideal look like?

### Unconstrained Visioning

```
Question: If I had unlimited time and resources, what would
          the perfect solution look like?

Purpose: Establish the north star, then work backward to
         find the closest practical approximation.
```

### Modular Decomposition

1. **Identify boundaries** — Where should modules split?
2. **Define interfaces** — How do modules communicate?
3. **Assign responsibilities** — What does each module do (and NOT do)?
4. **Map dependencies** — Which modules depend on which?
5. **Sketch data flows** — How does information move through the system?

### Blueprint Template

```markdown
## Module: [Name]
**Responsibility**: [Single clear purpose]
**Inputs**: [Data/signals it receives]
**Outputs**: [Data/signals it produces]
**Dependencies**: [What it needs from other modules]
**Boundaries**: [What it will NEVER do]

## Interface: ModuleA → ModuleB
Input type → Transformation → Output type
Error conditions → How handled

## Data Flow
User Input → Validator → Processor → Storage
                ↓            ↓          ↓
            [Schema]    [Transform]  [Persist]

## Edge Cases
- Empty input → return empty result
- Invalid format → raise ValidationError with specifics
- Partial success → return success + warnings list
- System overload → graceful degradation
```

### Design Principles

- **Single Responsibility** — Each module does ONE thing well
- **Open/Closed** — Open for extension, closed for modification
- **Dependency Inversion** — Depend on abstractions, not concretions
- **Least Surprise** — Behavior should match expectations

### Common Mistakes

- ❌ Over-engineering (too many abstractions too early)
- ❌ Under-engineering (monolithic "god objects")
- ❌ Not defining clear boundaries between modules

### Success Criteria

- Can draw architecture on a whiteboard
- Each module has single, clear responsibility
- Interfaces are obvious and inevitable
- Edge cases identified and addressed

---

## Stage 3: Ruthless Refinement (Rubric + Simplicity)

### What It Means

Define quality criteria, then eliminate everything non-essential.
> **Elegance is achieved when there's nothing left to take away.**

### Quality Rubric

| Criterion | Priority | Question |
|-----------|----------|----------|
| Simplicity | ⭐⭐⭐⭐⭐ | Could this be simpler without losing functionality? |
| Readability | ⭐⭐⭐⭐⭐ | Can a new team member understand this? |
| Maintainability | ⭐⭐⭐⭐ | Can this be changed without breaking unrelated code? |
| Robustness | ⭐⭐⭐⭐ | Does this handle all edge cases? |
| Test Coverage | ⭐⭐⭐⭐ | Are happy path, edges, and errors tested? |
| Performance | ⭐⭐⭐ | Does this meet performance requirements? |

### The 5-Step Refinement Process

1. **Identify Redundancy** — Where am I doing the same thing twice?
2. **Challenge Abstractions** — Does this abstraction earn its existence?
3. **Eliminate Fragility** — Where could this break?
4. **Remove Ambiguity** — Could someone misinterpret this code or name?
5. **Iterate** — Is there STILL something non-essential here?

### The "Could This Be Simpler?" Test

- Can I **remove** this entirely? (Best outcome)
- Can I **merge** this with something else? (Good)
- Can I make this **dumber/more obvious**? (Good)
- Can I **replace** with a standard library? (Sometimes)
- Do I need to **keep as-is**? (Last resort)

### Common Mistakes

- ❌ "Future-proofing" (complexity for imagined future needs)
- ❌ Premature optimization (performance before correctness)
- ❌ Clever code (impressiveness over clarity)
- ❌ "Enterprise" patterns (abstraction for abstraction's sake)

### Success Criteria

- No code exists that doesn't directly serve the goal
- A junior developer can understand the core logic
- Removing any component would break functionality
- The solution feels obvious in retrospect

---

## Stage 4: Masterful Execution (Plan → Craft → Verify)

### Plan (Before ANY code)

```markdown
# Task: [Clear, specific name]
## Goal
[What success looks like in 1-2 sentences]
## Implementation Plan
- [ ] Step 1: Set up basic structure
- [ ] Step 2: Implement core logic
- [ ] Step 3: Add error handling
- [ ] Step 4: Write tests (TDD where possible)
- [ ] Step 5: Integration testing
- [ ] Step 6: Performance validation
## Success Criteria
- [ ] All tests pass
- [ ] Performance meets requirements
- [ ] Documentation complete
```

### Craft: Naming Poetry

```python
# ❌ Bad: Unclear, abbreviated
def proc_dat(d): return d + 1

# ✅ Good: Clear intent
def increment_counter(current_count: int) -> int:
    return current_count + 1

# ✅ Great: Names reveal the domain
def calculate_next_fibonacci(previous: int, current: int) -> int:
    return previous + current
```

### Craft: Edge Case Handling

```python
def divide(a: float, b: float) -> Result[float, str]:
    if b == 0:          return Err("Cannot divide by zero")
    if math.isnan(a):   return Err("Cannot divide NaN values")
    if math.isinf(b):   return Err("Cannot divide infinite values")
    return Ok(a / b)
```

### Verify: The Non-Negotiables

```markdown
- [ ] All new code has tests
- [ ] All tests pass locally (not just CI)
- [ ] Edge cases tested
- [ ] Error conditions tested
- [ ] Feature works end-to-end
- [ ] No regressions in related features
- [ ] Linter passes
- [ ] No debug print statements
- [ ] No TODO/FIXME without tickets
- [ ] Would a staff engineer approve this?
```

### The Staff Engineer Test
>
> "If I showed this to a senior engineer I respect, would they approve it
> without significant changes?"
> If the answer is "no" or "maybe" — keep refining.

### Common Mistakes

- ❌ Writing code before planning
- ❌ Marking complete based on "it looks right"
- ❌ Skipping edge cases to "ship faster"
- ❌ No documentation ("the code is self-documenting")

---

## Stage 5: Crystallize the Vision (Final Reflection)

### What It Means

Make the invisible beauty of your thinking visible.
Document the journey, not just the destination.

### 1. Assumptions Ledger

```markdown
## Assumptions Made
- **Assumption**: [What you assumed]
  **Justification**: [Why you made this choice]
  **Risk**:       [What could go wrong]
  **Mitigation**: [How you handled it]

## Design Choices
- **Chose**:     [Technology/approach A] over [B]
  **Reason**:    [Why]
  **Trade-off**: [What you gave up]
```

### 2. Simplification Story

```markdown
## Complexity Removed
1. **Removed**: [X] (N lines)
   **Why**:     [Reason]
   **Impact**:  [Effect on codebase]

## Abstractions Streamlined
- Before:  [Old structure]
- After:   [New structure]
- Benefit: [What improved]
```

### 3. Inevitability Argument

```markdown
## Why This Solution is Inevitable
The core challenge was [X], requiring [Y]. Any solution must:
1. Handle [constraint A]
2. Support [requirement B]
3. Integrate with [system C]

Given these constraints, [our solution] is the simplest design that works.
Any other approach adds unnecessary complexity without meaningful benefit.
```

### 4. Meaningful Commits

```bash
# ❌ Bad
git commit -m "fix bug"

# ✅ Good
git commit -m "feat: add email validation with comprehensive error messages

- Validates format using RFC 5322 standard
- Returns specific error for malformed addresses
- Adds 15 new test cases covering edge cases

Closes #123"
```

### 5. Capture Lessons

Run `python scripts/capture_lesson.py` if any corrections occurred.

### Common Mistakes

- ❌ Not documenting decisions ("everyone knows this")
- ❌ Not explaining "why" (only documenting "what")
- ❌ Generic commit messages (information loss over time)

### Success Criteria

- Someone can understand your thinking 6 months from now
- Decisions have clear rationale attached
- Git history tells a coherent story

---

## Success Metrics

A project using ultrathink succeeds when:
- ✅ **Inevitability** — The solution feels obvious in retrospect
- ✅ **Simplicity** — Explainable to a new team member in 10 minutes
- ✅ **Robustness** — Handles edge cases gracefully
- ✅ **Maintainability** — Future changes are easy to implement
- ✅ **Beauty** — The code/design makes you proud
