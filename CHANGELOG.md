# Changelog

## [0.9.9.1] - 2026-04-05

### Added
- `single_agent/afrp/SKILL.md` — Audience-First Response Protocol as mandatory pre-router gate (query classification A/B/C/D × audience level)
- `single_agent/cidf/SKILL.md` — CIDF v1.2 as a loadable sub-skill (on top of runnable package)
- `api_server.py` — Stateless `POST /ultrathink` REST endpoint on port 8001, Pydantic V2, `model_hint` field (ADR-001)
- `.claude/skills/ultrathink-system/SKILL.md` — ECC-generated repo conventions skill (separate from mother skill)
- `.agents/skills/ultrathink-system/agents/openai.yaml` — Codex skill metadata
- `.claude/commands/ecc-sync.md` + `feature-development.md` — ECC workflow commands
- `.claude/ecc-tools.json` — ECC managed file manifest (tier: free, packages: runtime-core + workflow-pack)
- `.claude/identity.json` — ECC identity baseline
- `.claude/lessons/LESSONS.md` — Cross-session shared knowledge base
- `.claude/homunculus/instincts/inherited/ultrathink-system-instincts.yaml` — 7 continuous-learning-v2 instincts
- `.codex/config.toml` + `AGENTS.md` + `agents/*.toml` — Codex harness config
- `.github/workflows/ci.yml` — CI pipeline
- `.claude/agents/ultrathink-*.md` — 7 multi-agent SKILL.md files at Claude Code native subagent path
- `.agents/skills/ultrathink-system/` — Codex/OpenCode auto-load path

### Changed
- Renamed `single-agent/` → `single_agent/` (snake_case, aligns with Python package conventions)
- Renamed `multi-agent/` → `multi_agent/` (snake_case, aligns with Python package conventions)
- `CLAUDE.md` rewritten to match live repo: continuous-learning, AFRP gate, stateless API, companion repo refs
- `single_agent/SKILL.md` Mode Router now references AFRP gate as mandatory first step
- All internal path references updated to `single_agent/` + `multi_agent/`

### Fixed
- Multi-agent SKILL.md files were source-only — now committed to `.claude/agents/` (Claude Code native runtime path)
- Version alignment: `single_agent/SKILL.md` was v2.0.0, now v0.9.9.1 (matches repo versioning scheme)

---


All notable changes to ultrathink System are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
Versioning follows [Semantic Versioning](https://semver.org/).

---

## [1.0.0] - 2026-03-20

### Added
- Initial public release
- **Single-agent package**: Complete ultrathink SKILL.md for Claude Code, Cowork, and Open
- **Multi-agent network**: 7 specialized agents (Orchestrator, Context, Architect, Refiner, Executor, Verifier, Crystallizer)
- **References**: 4 deep-dive documents (5-stages, directives, content-insertion, skill-architecture)
- **Scripts**: `verify_before_done.py`, `capture_lesson.py`, `create_task_plan.sh`
- **Templates**: `task-plan.md`, `lessons-log.md`, `verification-checklist.md`
- **Multi-agent shared utilities**: `state_manager.py`, `message_bus.py`, `ultrathink_core.py`
- **MCP servers**: `ultrathink_orchestration_server.py`, `agent_communication_server.py`
- **Config**: `agent_registry.json`, `routing_rules.json`
- **Examples**: financial-validator, api-integration, architecture-refactor
- **Docs**: installation, quick-start, single-agent guide, multi-agent guide, API reference, troubleshooting, FAQ
- **Tests**: test_single_agent.py, test_multi_agent.py, test_orchestrator.py
- **Installation scripts**: `install-single-agent.sh`, `install-multi-agent.sh`
- **Verification**: `verify-package.sh`
- Apache 2.0 license

### Features in v1.0.0
- ultrathink 5-stage methodology (Context → Architecture → Refinement → Execution → Crystallization)
- 6 core operational directives always active
- Content Insertion Decision Framework v2 (simplicity-first, 5 ranked methods)
- SKILL.md architecture standards (< 500 lines, progressive disclosure)
- Multi-agent orchestration with parallel execution
- Self-improvement loop via lessons.md
- Verification-before-done protocol (never visual-only)
- Cross-platform: Claude Code, Cowork, Clawdbot, MoltBot, OpenClaw

---

## [Unreleased]

### Planned
- Additional example projects (DevOps, data pipeline, API design)
- Video walkthrough tutorials
- Community skill registry integration
- Performance benchmarks and token ROI measurements
- Clawdbot-specific configuration wizard
- Integration tests with real agent frameworks
- Lessons database (shared anonymized patterns)
