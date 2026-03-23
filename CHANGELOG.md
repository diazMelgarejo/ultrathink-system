# Changelog

All notable changes to ultrathink System are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
Versioning follows [Semantic Versioning](https://semver.org/).

---

## [0.9.4.1] - 2026-03-23

### Fixed
- Directory naming convention: renamed `multi-agent/` → `multi_agent/` and `single-agent/` → `single_agent/` for valid Python package imports
- Updated pyproject.toml wheel package list to use underscore names
- Updated all tests, imports, and documentation references to underscore naming
- Fixed routing_rules.json CIDF policy paths

### Added
- `test-package-install.py`: validates package metadata and pip install functionality
- GitHub Actions CI workflow (`.github/workflows/ci.yml`) with pytest, build, and lint stages

### Verified
- 86 unit tests passing
- sdist and wheel builds successful
- Package install and import functionality working

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
- **Docs**: installation, quick-start, single_agent guide, multi_agent guide, API reference, troubleshooting, FAQ
- **Tests**: test_single_agent.py, test_multi_agent.py, test_orchestrator.py
- **Installation scripts**: `install-single_agent.sh`, `install-multi_agent.sh`
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
