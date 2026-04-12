# ultrathink — Claude Skill Package

> The ultrathink 5-stage methodology, AFRP pre-router gate, CIDF v1.2 content insertion
> framework, and 7-agent execution network — distilled into an installable Claude skill.

## One-Click Install

### Option A: Remote install (recommended)

```bash
curl -sL https://raw.githubusercontent.com/diazMelgarejo/ultrathink-system/main/install.sh | bash
```

### Option B: Local install (if you've cloned the repo)

```bash
cd ultrathink-system/
bash install.sh
```

### Option C: Project-local install

```bash
cd your-project/
bash /path/to/ultrathink-system/install.sh --project
```

### Option D: Manual install

```bash
# Copy the skill folder to your Claude skills directory
cp -R bin/skills ~/.claude/skills/ultrathink-system
```

## What Gets Installed

```
~/.claude/skills/ultrathink-system/
├── SKILL.md                              <- Master skill (5-stage + router + 6 directives)
├── afrp/
│   └── SKILL.md                          <- Audience-First Response Protocol (pre-router gate)
├── cidf/
│   └── SKILL.md                          <- Content Insertion Decision Framework v1.2
├── references/
│   ├── amplifier-principle.md            <- Foundational essay: intent-driven development
│   ├── ultrathink-5-stages.md            <- Deep dive: 5-stage methodology
│   ├── core-operational-directives.md    <- Deep dive: the 6 directives
│   ├── content-insertion-framework.md    <- CIDF human reference + JSON policy
│   └── skill-architecture-guide.md       <- How to build SKILL.md files
├── templates/
│   ├── task-plan.md                      <- Directive #1: task planning template
│   ├── verification-checklist.md         <- Directive #4: pre-completion checklist
│   └── lessons-log.md                    <- Directive #3: self-improvement log
├── scripts/
│   ├── verify_before_done.py             <- Directive #4: programmatic verification
│   ├── capture_lesson.py                 <- Directive #3: capture lessons interactively
│   └── create_task_plan.sh              <- Directive #1: generate task plans
└── config/
    ├── agent_registry.json               <- Mode 3: 7-agent network definition
    └── routing_rules.json                <- Mode 3: message routing rules
```

**16 files** total. The skill auto-activates in Claude Code CLI and Claude Desktop.

## How It Works

### Auto-Activation

Claude detects the skill from `~/.claude/skills/ultrathink-system/SKILL.md` and loads it
when your query matches the description triggers:

- "ultrathink", "think deeply", "5-stage"
- "systematic approach", "elegant solution"
- "verify before done", "content insertion"
- Architectural thinking, complex multi-step tasks

### Progressive Disclosure

The master SKILL.md stays under 220 lines. Deeper context is loaded on-demand
from `references/`, `afrp/`, and `cidf/` — keeping your context window clean.

### The 3 Execution Modes

| Mode | When | What Happens |
|------|------|-------------|
| **Mode 1** Inline | 1-2 steps, single file | Direct execution, no subagents |
| **Mode 2** + Subagents | 3-7 steps, 1-2 systems | Full 5-stage process with delegation |
| **Mode 3** Network | 8+ steps, 3+ systems | 7-agent parallel execution network |

### The 5 Stages (Mode 2+)

1. **Context Immersion** — Ground yourself deeply before proposing solutions
2. **Visionary Architecture** — Design the most elegant modular solution
3. **Ruthless Refinement** — Eliminate everything non-essential
4. **Masterful Execution** — Plan, craft with TDD, verify programmatically
5. **Crystallize the Vision** — Document decisions, capture lessons

### The 6 Directives (Always Active)

1. **Plan Node** — Write todo.md before any 3+ step task
2. **Subagents** — Offload when context > 70%
3. **Self-Improve** — Capture lessons after corrections
4. **Verify First** — Never mark done without programmatic proof
5. **Elegance** — Pause: "Is there a more elegant way?"
6. **Autonomous Fix** — Bug report -> investigate -> fix -> verify -> report

## Using the Scripts

```bash
# Create a task plan (Directive #1)
bash ~/.claude/skills/ultrathink-system/scripts/create_task_plan.sh "Build auth system"

# Verify before marking done (Directive #4)
python3 ~/.claude/skills/ultrathink-system/scripts/verify_before_done.py --task "Auth system" --dir .

# Capture a lesson (Directive #3)
python3 ~/.claude/skills/ultrathink-system/scripts/capture_lesson.py
```

## Uninstall

```bash
bash install.sh --uninstall
# or manually:
rm -rf ~/.claude/skills/ultrathink-system
```

## Source

Distilled from [diazMelgarejo/ultrathink-system](https://github.com/diazMelgarejo/ultrathink-system)
bin/skills/SKILL.md v0.9.9.6 -> unified install script v1.1.0
