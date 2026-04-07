# ultrathink Single-Agent Skill
**Quick Start for Claude Code, coworker, and OpenClaw**

---

## Installation

```bash
# Claude Code
cp -r . ~/.claude/skills/ultrathink-system-skill

# Cowork
cp -r . ~/.cowork/skills/ultrathink-system-skill

# Symlink (easier updates)
ln -s $(pwd) ~/.claude/skills/ultrathink-system-skill
```

## Activation

```
ultrathink this
apply the system to: [your task]
use the methodology for: [problem]
```

Auto-triggers on: "complex task", "architect", "production-ready", "elegant solution", "verify before done"

## Files

| File | Purpose |
|------|---------|
| `SKILL.md` | Main intelligence layer — loaded by agent |
| `references/ultrathink-5-stages.md` | Deep dive: 5-stage methodology |
| `references/core-operational-directives.md` | Deep dive: 6 directives |
| `references/content-insertion-framework.md` | Simplicity-first insertion |
| `references/skill-architecture-guide.md` | How to create new skills |
| `scripts/verify_before_done.py` | Pre-completion verification |
| `scripts/capture_lesson.py` | Self-improvement loop |
| `scripts/create_task_plan.sh` | Task plan generator |
| `templates/task-plan.md` | Planning template |
| `templates/lessons-log.md` | Lessons tracking |
| `templates/verification-checklist.md` | Manual verification checklist |

## Quick Scripts

```bash
# Create a task plan
./scripts/create_task_plan.sh "Build auth system"

# Verify before marking done
python scripts/verify_before_done.py --task "Build auth system"

# Capture a lesson after a correction
python scripts/capture_lesson.py
```

## Compatibility

| Platform | Status |
|---------|--------|
| Claude Code | ✅ Native |
| Cowork | ✅ Native |
| Open / claude.ai | ✅ Manual activation |
| ECC Tools | ✅ Drop into skills/ |
| everything-claude-code | ✅ Compatible |

---

*See root README.md for full documentation.*
