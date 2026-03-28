# Changelog

All notable changes to ultrathink System are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
Versioning follows [Semantic Versioning](https://semver.org/).

---


## [0.9.6.0] - 2026-03-27

### Added
- **LAN Continuity**: LAN Detect & Resume synchronized with Perplexity-Tools [SYNC]
- **Spawn Reconciliation**: Layer 2 spawn reconciliation to prevent redundant model spawns [SYNC]
- **Distributed State**: Shared Redis state for global session tracking across LAN
- **CIDF Sub-skill**: `cidf/SKILL.md` with recursive sub-skill loading and agent discovery
- **CIDF DESIGN.md**: Original design document with flowcharts, decision matrices, meta-lesson
- **Amplifier Principle**: Foundational philosophy document in `references/amplifier-principle.md`
- **AFRP**: Audience-First Response Protocol integrated as mandatory pre-router gate in `single_agent/afrp/SKILL.md`
- `api_server.py` updated to v0.9.6.0 with GPU reconciliation via PT `/reconcile` endpoint

### Changed
- `single_agent/SKILL.md` updated to v0.9.6.0 with LAN continuity and reconciliation sections
- Phase transitions hardened to be resume-aware
- `pyproject.toml` version aligned to 0.9.6.0
- CIDF README.md updated with DESIGN.md in package structure

### Synced with Perplexity-Tools
- Both repos synchronized to v0.9.6.0
- Network config harmonized (Windows 192.168.1.100, Mac 192.168.1.101)
- Cross-repo SKILL.md references with recursive loading pointers

## [0.9.5.0] - 2026-03-27

### Added
- Multi-computer orchestration workflow with full hardware profile awareness
- LAN-wide AI model discovery and takeover recruitment logic (lan_discovery.py)
- ECC and autoresearch spawn reconciliation registry (spawn_reconciliation.py)
- P2 hardening: Expanded test infrastructure and CI/CD pipelines
- Full repository-wide version synchronization to 0.9.5.0

## [0.9.4.3] - 2026-03-26

### Fixed
- Root docs now use the real installer filenames: `install-single-agent.sh` and `install-multi-agent.sh`
- `verify-package.sh` now validates the CIDF package before reporting final pass/fail
- Package install verification now uses a local build-plus-wheel-install flow that works offline when tooling is present
- Repository-root docs now distinguish `single_agent/scripts/...` commands from installed-skill `scripts/...` commands

### Changed
- Declared Hatchling explicitly as the build backend
- Aligned current package metadata, skill/config versions, and user-facing release surfaces to `0.9.4.3`
- Expanded ignore rules for repo-local build outputs and disposable test environments

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
