# Lessons Learned — Self-Improvement Log
**ultrathink System — Directive #3: Self-Improvement Loop**
**Project**: [Project Name]
**Started**: YYYY-MM-DD

> This file is the institutional memory of this project.
> Every lesson written here prevents the same mistake from recurring.
> **Review this file at the start of each session.**
> Add entries with: `python scripts/capture_lesson.py`

---

## Usage

### Adding a Lesson (Interactive)
```bash
python scripts/capture_lesson.py
```

### Adding a Lesson (Quick)
```bash
python scripts/capture_lesson.py --pattern "Premature Optimization"
```

### Reviewing All Lessons
```bash
python scripts/capture_lesson.py --review
```

### Viewing Statistics
```bash
python scripts/capture_lesson.py --stats
```

---

## Lesson Format

Each entry follows this structure:

```markdown
## YYYY-MM-DD — [Pattern Name]

### What Went Wrong
[Specific description of the mistake]

### Root Cause
[Why did this happen? What was misunderstood?]

### Prevention Rule
[How to avoid this in the future — must be actionable]

### Verification Trigger
[Question to ask yourself BEFORE making this mistake again]

### Applied To
[Future scenarios where this lesson applies]

### Examples
✅ Good: [What to do instead]
❌ Bad: [What was done wrong]
```

---

## Common Categories

| Category | Description |
|----------|-------------|
| Premature Optimization | Added complexity without measuring first |
| Insufficient Error Handling | Didn't handle all failure modes |
| Visual Verification | Trusted appearance over programmatic check |
| Missing Edge Case | Forgot to handle boundary conditions |
| Incorrect Requirement Assumption | Misunderstood what was needed |
| Over-Engineering | Added abstractions that weren't justified |
| Under-Engineering | Too simple, didn't scale to actual problem |
| Skipped Planning | Started coding without a written plan |
| Test Coverage Gap | Core path or edge case had no test |
| Naming Clarity Issue | Name didn't reveal intent, caused confusion |

---

## Session Review Checklist

Before starting work each session, scan for:
- [ ] Any patterns relevant to today's task
- [ ] Mistakes I've made before in this domain
- [ ] Rules that apply to the current task type

---

## Entries

<!-- Entries are appended below by capture_lesson.py -->
<!-- Format: ## YYYY-MM-DD — [Pattern Name] -->

