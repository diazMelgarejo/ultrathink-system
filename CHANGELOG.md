# Changelog

## [0.9.9.4] - 2026-04-11
### Changed
- Version: synchronized active package and skill metadata to 0.9.9.4
- Docs: `README.md`, `CLAUDE.md`, `docs/PERPLEXITY_BRIDGE.md`, and `docs/SYNC_ANALYSIS.md` now reference the active `bin/orama-system/SKILL.md` path and current version
- Docs: `portal_server.py` and `network_autoconfig.py` are now documented as active LAN/runtime helpers
- Runtime defaults: LAN helper defaults now align with the canonical Mac/Win LM Studio endpoints used by Perplexity-Tools
- Historical `0.9.9.0` and `1.0.0-rc` notes preserved below for context

## [0.9.9.3] - 2026-04-07
### Changed
- Docs: all `single_agent/` path references updated to `bin/orama-system/` across README, docs/, .claude/, .agents/, .codex/, .github/, bin/orama-system/ skills files
- Docs: `install-single-agent.sh` references updated to `install.sh`
- Docs: all `single-agent` concept labels updated to `bin/orama-system`
- Version: synchronized to 0.9.9.3 across all agent.md frontmatter, SKILL.md, CLAUDE.md, INSTALL.md
- CHANGELOG.md: historical entries for pre-0.9.9.3 versions intentionally preserved as-is

## [0.9.9.2] - 2026-04-06
### Fixed
- CI: restored missing dependencies (`fastapi`, `httpx`) in runner environment
- Docs: restored required transport markers for `test_bridge_docs.py` regression tests
- api_server.py: restored missing attributes and legacy logic to passing `test_api_server.py`
- Version: synchronized all files to 0.9.9.2

## [0.9.9.1] - 2026-04-06
### Added
- 7 Claude Code native subagent files at `.claude/agents/ultrathink-*.md`
- Harness path map in `CLAUDE.md` (section 7) — source→runtime→global paths
- CIDF v1.2 canonical source in `single_agent/cidf/`; install scripts copy idempotently
- Reference docs in `.agents/skills/orama-system/references/`
### Changed
- `install-multi-agent.sh`: deploy to `.claude/agents/` + `~/.claude/agents/` + platform dirs
- `install-single-agent.sh`: harness path map; CIDF installed idempotently to all runtime locations
- `CLAUDE.md`: section 7 (Harness Path Map) added; AutoResearcher Integration (section 4) preserved
- `agent_registry.json`: version bumped to 0.9.9.1; all routing and autoresearch_agents preserved
### Fixed
- Install scripts: agents now correctly deployed to `.claude/agents/` (Claude Code native path)

---


All notable changes to The ὅραμα System are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
Versioning follows [Semantic Versioning](https://semver.org/).

---

## [1.0.0-rc] - 2026-03-31 [SYNC]

### Added
- `multi_agent/mcp_servers/lmstudio_bridge.py` — async httpx LM Studio client
- `multi_agent/mcp_servers/lmstudio_mcp_server.py` — MCP stdio server:
  `lmstudio_chat`, `lmstudio_list_models`, `lmstudio_orchestrate`, `lmstudio_health`
- `portal_server.py` — LAN portal port 8002, slate-grey (#475569), white text
- `multi_agent/config/mcp.json` — LM Studio plugin registration

### Changed
- `.env.example` — LM Studio vars + canonical model IDs documented

### Architecture (v1.0 RC)
- Mac = Orchestrator + Final Validator/Presenter (context=4096)
- Windows = UltraThink Agent (all roles, sequential or 1-4 parallel)
- Orchestration cycle: Mac dispatches → Win works → Mac validates →
  optional cloud verify (online + budget) → Mac presents → repeat

### Canonical Models [SYNC]
- Win: Qwen3.5-27B Q4_K_M, GPU Offload=40, Context=16384
  (also loadable in Ollama/koboldcpp — backend-agnostic GGUF)
- Mac: Qwen3.5-9B-MLX-4bit, Metal full offload, Context=4096
  (conservative, safe on M2 16GB; weights compatible with Ollama)

---

---

## [1.0-rc] - 2026-03-30 [SYNC]

### Changed
- HTTP bridge (`POST /ultrathink`, `api_server.py`) confirmed as v1.0 RC primary transport.
  Docs corrected across `PERPLEXITY_BRIDGE.md`, `SYNC_ANALYSIS.md`, `api-reference.md`,
  `faq.md`, and `ROADMAP_v1.1.md` to reflect this.

### Synced with Perplexity-Tools [SYNC]
- PT added `orchestrator/ultrathink_mcp_client.py` (MCP-Optional Tier 1 client infrastructure)
- PT async httpx fix: `httpx.post()` → `httpx.AsyncClient` in bridge wrapper
- `"transport": "mcp" | "http"` key now surfaced in PT `/orchestrate` response
- MCP `_solve()` remains a stub here — PT client detects stub and falls back to HTTP
- Tier 2 (real `_solve()` pipeline) tracked in `docs/ROADMAP_v1.1.md`

---

## [0.9.9.0] - 2026-03-30

### Added
- **v1.1+ Roadmap**: `docs/ROADMAP_v1.1.md` documenting deferred MCP-first transport and Redis coordination
- **Bridge Contract**: `multi_agent/shared/bridge_contract.py` — shared mapping between MCP `optimize_for` and HTTP `reasoning_depth`

### Changed
- api_server.py hardened: OLLAMA_FALLBACK default corrected, duplicate lines removed, Pydantic validators tightened
- Architecture documentation clarified: ultrathink is stateless, HTTP bridge is the MVP transport, MCP over stdio deferred to v1.1+

### Fixed
- Version alignment: all files synchronized to 0.9.9.0

### Synced with Perplexity-Tools
- Both repos synchronized to v0.9.9.0 [SYNC]
- HTTP bridge made always-active in PT (opt-in flag removed) [SYNC]
- MCP-first transport deferred to v1.1+ in both repos [SYNC]

---

## [0.9.8.0] - 2026-03-29

### Security

- **api_server.py**: Rate limiting via `slowapi` (OWASP API4) [SYNC]
- **api_server.py**: Input validation — bounded `task_description` with `max_length=8000` and `ALLOWED_HOSTS` middleware [SYNC]
- **api_server.py**: Timeout clamped to 1–600 s range to prevent misconfiguration
- **api_server.py**: Internal IPs not exposed in health endpoint (OWASP API8) [SYNC]

### Fixed

- **api_server.py**: Migrated `@validator` to Pydantic V2 `@field_validator` + `@classmethod` (deprecation fix) [SYNC]

### Synced with Perplexity-Tools

- Both repos synchronized to v0.9.8.0 [SYNC]
- `orchestrator.py` receives same security hardening and Pydantic V2 migration [SYNC]

---


## [0.9.7.0] - 2026-03-28

### Added
- **AFRP**: Audience-First Response Protocol — mandatory pre-router gate at `single_agent/afrp/SKILL.md` [SYNC]
  - 7-step protocol: Stop → Classify → Clarify → Separate Profile → Scope → Calibrate → Slop Test
  - Machine-caller escape path for programmatic invocation via `POST /ultrathink`
  - Failure mode taxonomy with 6 named anti-patterns and recovery procedures
  - Cross-skill integration docs (Router, CIDF, Amplifier Principle relationships)
- **AFRP failure-modes.md**: Extended failure mode reference with diagnostic decision tree
- **AFRP README.md**: Quick-start and package structure

### Changed
- `single_agent/SKILL.md`: Pre-Router Gate section added before Execution Mode Router
- `single_agent/cidf/SKILL.md`: "Relationship to AFRP" section with loading order
- All 14 multi_agent subsystem files aligned from v0.9.4.3 to v0.9.7.0

### Fixed
- `.github/workflows/ci.yml`: Standardized `setup-python@v4` → `setup-python@v5`
- Removed empty/premature v0.9.7.0 changelog header in SKILL.md

### Synced with Perplexity-Tools
- Both repos synchronized to v0.9.7.0 [SYNC]
- AFRP cross-referenced in PT SKILL.md 4-layer architecture table [SYNC]

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
- **Single-agent package**: Complete ultrathink SKILL.md for Claude Code, coworker, and OpenClaw
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
