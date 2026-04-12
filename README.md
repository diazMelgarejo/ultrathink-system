# ultrathink System

> *"Technology married with humanities yields solutions that make hearts sing."*

**The complete agent methodology for solving impossible problems with elegance.**

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![SKILL.md Standard](https://img.shields.io/badge/SKILL.md-Compatible-green)](https://ecc.tools/skills)
[![ECC Tools](https://img.shields.io/badge/ECC_Tools-Compatible-brightgreen)](https://ecc.tools)
[![Version](https://img.shields.io/badge/version-0.9.9.7-orange)](CHANGELOG.md)

**Compatible with**: Claude Code · Cowork · Clawdbot · MoltBot · OpenClaw · ECC Tools · everything-claude-code

---

## What This Is

A production-ready, self-improving agent skill package that synthesizes:

| Component | What it provides |
|-----------|-----------------|
| **ultrathink 5-Stage Methodology** | Context → Architecture → Refinement → Execution → Crystallization |
| **6 Core Operational Directives** | Plan · Subagents · Self-Improvement · Verification · Elegance · Autonomous Bug Fixing |
| **Content Insertion Framework v2** | Simplicity-first ranked approach to data/content operations |
| **SKILL.md Architecture Standard** | How to author production-grade agent skills |
| **Multi-Agent Network** | 7 specialized agents for distributed parallel problem solving |

### The Amplifier Principle

AI doesn't replace judgment, it amplifies intent: ultrathink gives that intent structure. Clear methodology → clear output. Vague intent → scaled ambiguity.

---

## Quick Start (3 Minutes)

```bash
# 1. Install bin/skills (Claude Code / Cowork / OpenClaw)
./install.sh

# 2. Activate in Claude
# "ultrathink this"
# "Apply ultrathink system to: [your task]"

# 3. Create a task plan
./bin/skills/scripts/create_task_plan.sh "Build my feature"

# 4. Verify before marking done
python bin/skills/scripts/verify_before_done.py --task "Build my feature"
```

---

## Repository Structure

```ascii
ultrathink-system/
│
├── bin/skills/                   ← Install here for Claude Code / Cowork
│   ├── SKILL.md                    ← Main intelligence layer (<500 lines)
│   ├── references/                 ← Deep-dive documentation
│   │   ├── ultrathink-5-stages.md
│   │   ├── core-operational-directives.md
│   │   ├── content-insertion-framework.md
│   │   └── skill-architecture-guide.md
│   ├── scripts/                    ← Automation tools
│   │   ├── verify_before_done.py   ← Pre-completion verification
│   │   ├── capture_lesson.py       ← Self-improvement loop
│   │   └── create_task_plan.sh     ← Task plan generator
│   └── templates/                  ← Reusable task / lesson templates
│
├── bin/                    ← Install here for Clawdbot / OpenClaw
│   ├── agents/                     ← 7 specialized agents
│   │   ├── orchestrator/           ← Coordinates 5-stage process
│   │   ├── context/                ← Stage 1: Context Immersion
│   │   ├── architect/              ← Stage 2: Visionary Architecture
│   │   ├── refiner/                ← Stage 3: Ruthless Refinement
│   │   ├── executor/               ← Stage 4: Masterful Execution (parallelizable)
│   │   ├── verifier/               ← Stage 4.5: Verification Before Done
│   │   └── crystallizer/           ← Stage 5: Crystallize the Vision
│   ├── shared/                     ← Core types + state + messaging
│   ├── config/                     ← Agent registry + routing rules
│   └── mcp_servers/                ← MCP server implementations
│
├── examples/                       ← Real-world usage walkthroughs
├── docs/                           ← Installation, guides, FAQ
├── portal_server.py                ← LAN dashboard for PT, ultrathink, LM Studio, Ollama
├── network_autoconfig.py           ← LAN IP / agent auto-discovery helper
├── tests/                          ← Full test suite (pytest)
└── .github/                        ← CI/CD workflows
```

---

## Installation

### Single-Agent (Most Users)

```bash
./install.sh
```

| Platform | Directory |
|---------|-----------|
| Claude Code | `~/.claude/skills/ultrathink-system/` |
| Cowork | `~/.cowork/skills/ultrathink-system/` |
| ECC Tools | `~/.claude/skills/ultrathink-system/` |
| everything-claude-code | Drop into skills dir |

### Multi-Agent Network (Distributed / Parallel)

```bash
./install-multi-agent.sh
python bin/mcp_servers/ultrathink_orchestration_server.py
```

### LAN Helpers

```bash
# Probe a LAN-friendly host/IP and optionally scan for agents
python network_autoconfig.py --scan

# Launch the slate-grey portal on port 8002
python portal_server.py
```

- `network_autoconfig.py` detects the preferred local IP and can scan for LM Studio, Ollama, PT, ultrathink, and portal services.
- `portal_server.py` shows a lightweight LAN dashboard for PT, ultrathink, LM Studio, and Ollama endpoints.

---

## The 5-Stage Process

```
1. Context Immersion    — Scan git, docs, patterns, constraints. Understand before acting.
2. Visionary Architecture — Design the most elegant solution. Decompose modularly.
3. Ruthless Refinement — Eliminate everything non-essential. Elegance = nothing left to remove.
4. Masterful Execution — Plan → Craft (TDD) → Verify (programmatic, not visual).
5. Crystallize Vision  — Assumptions ledger, simplification story, inevitability argument.
```

---

## The 6 Operational Directives

Always active, regardless of which stage you're in:

| # | Directive | Trigger |
|---|-----------|---------|
| 1 | 📋 **Plan Node Default** | Any task with 3+ steps |
| 2 | 🤖 **Subagent Strategy** | When context window is crowded |
| 3 | 🔄 **Self-Improvement Loop** | After ANY user correction |
| 4 | ✅ **Verification Before Done** | Before marking any task complete |
| 5 | ✨ **Demand Elegance** | When a solution feels hacky |
| 6 | 🔧 **Autonomous Bug Fixing** | On any bug report |

---

## Multi-Agent Architecture

```ascii
User → Orchestrator
           ↓
    Context Agent           ← Stage 1 (spawns sub-agents)
           ↓
    Architect Agent         ← Stage 2 (spawns module designers)
           ↓
    Refiner Agent           ← Stage 3 (loops until elegance ≥ 0.8)
           ↓
  ┌──────────────────┐
  │Executor Agent × 5│      ← Stage 4 (parallel)
  └──────────────────┘
           ↓
    Verifier Agent          ← Stage 4.5 (blocks until PASS)
           ↓
    Crystallizer Agent      ← Stage 5 (documents + captures lessons)
           ↓
    Result + Lessons
```

---

## Self-Improvement System

```bash
# After any mistake or user correction:
python scripts/capture_lesson.py

# Review before starting work:
python scripts/capture_lesson.py --review

# Analyze your mistake patterns:
python scripts/capture_lesson.py --stats
```

Lessons compound over time. Mistake rate measurably declines.

---

## ECC Tools Integration

This skill follows the SKILL.md open standard and is compatible with
[ECC Tools](https://ecc.tools) (65+ skills, 16 agents, 102 AgentShield security rules).

```bash
# Add to your ECC profile
cp -r bin/skills ~/.claude/skills/ultrathink-system

# Then use with any ECC-compatible harness
```

---

## Success Metrics

| Metric | Target |
|--------|--------|
| Token ROI | > 10:1 |
| Trigger Accuracy | > 95% |
| Boundary Violations | 0 |
| Verification Before Done | 100% |
| Repeat Mistake Rate | < 5% (declining) |

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Apply ultrathink to your contributions.
Run `./verify-package.sh` before submitting a PR.

**High-value contributions**: new examples, additional reference docs, platform integrations,
lessons-learned patterns, security improvements.

---

## License

Apache License 2.0 — use freely in commercial and private projects.
See [LICENSE](LICENSE).

---

## GitHub Topics

`ai-agents` `claude` `claude-code` `skill-md` `prompt-engineering` `ultrathink`
`agent-framework` `ecc-tools` `openclaw` `clawdbot` `mcp` `self-improving`

---

*"The people crazy enough to believe they can change the world are the ones who do."* 🚀
