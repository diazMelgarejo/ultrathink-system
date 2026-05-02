# Legacy Agent Resume (Archived from v1.0 RC)
> Original Version: Commit 73e0031
> Reason for archive: Transition to v2; preserved for 4-tier discovery logic extraction.

# orama-system — Agent Resume

### Hardware Safety & Model Affinity (2026-04-26)

**Canonical policy:** `../perplexity-api/Perpetua-Tools/config/model_hardware_policy.yml`

Hard rules — never override:
- Windows-only (NEVER_MAC): `gemma-4-26b-a4b-it`, `gemma-4-26B-A4B-it-Q4_K_M`,
  `qwen3.5-27b-claude-4.6-opus-reasoning-distilled-v2`
- Mac-only (NEVER_WIN): `gemma-4-e4b-it`, `qwen3.5-9b-mlx`, `qwen3.5-9b-mlx-4bit`

Runtime validation fires at three layers (L1 discover, L2 manager/launcher,
L3 API). Any `HardwareAffinityError` must escalate to Controller — never
silently fallback to unsafe hardware.

If you are an AI agent reading this: do NOT add unverified model IDs to any
policy file or config. Confirm with `discover.py --status` on actual hardware
first. Known hallucinations removed: `qwen3-coder-14b` and `gemma4:e4b`.

---

## Status: COMPLETE ✅ (2026-04-20/21)

All automation from the LM Studio Auto-Discovery plan has been implemented and verified.

---

## What Was Done

### Layer A — ~/.openclaw/scripts/discover.py
- Installed by `setup_macos.py` (step 5) on every run
- Idempotent: skips writes when hash unchanged
- 4-tier disaster recovery: live probe → last_discovery.json → backups → profiles
- File-lock safe for concurrent Claude Code sessions
- **Bug fixes applied in Task 15 dry-run:**
  - `win_primary` selection: now correctly prefers `qwen3.5-27b` over alphabetically-first gemma
  - `recovery_tier` in hash-match path: now updated even when endpoints unchanged

### Tests: 12/12 passing
`~/.openclaw/scripts/tests/test_discover.py` (also in `scripts/tests/test_discover.py`)

### .claude/ Automations
| Type | File | Status |
|------|------|--------|
| Hook: SessionStart | `.claude/settings.json` | ✅ discover-lm-studio.sh async |
| Hook: PostToolUse | `.claude/settings.json` | ✅ ruff check on .py edits |
| Hook: Stop | `.claude/settings.json` | ✅ lessons check |
| Skill | `.claude/skills/ecc-sync/SKILL.md` | ✅ promoted from commands/ |
| Skill | `.claude/skills/agent-methodology/SKILL.md` | ✅ Claude-only 5-stage methodology |
| Subagent | `.claude/agents/crystallizer.md` | ✅ stage 1 of 5 |

### Discovery Hub Chain
```
SessionStart → scripts/discover-lm-studio.sh (Layer B)
    → checks ~/.openclaw/state/discovery.json age
    → if stale: python3 ~/.openclaw/scripts/discover.py
        → probes localhost:1234 + subnet scan 192.168.254.0/24
        → updates openclaw.json, devices.yml, models.yml, .env.lmstudio
```

### Current Live State (last verified 2026-04-21)
- Mac LM Studio: `localhost:1234` — 3 models (gemma-4-e4b-it, qwen3.5-9b-mlx, embed)
- Win LM Studio: `192.168.254.105:1234` — 5 models (Win offline → using preserved last-good)
- Recovery tier: 1 (config preserved from last live probe)
- `LMS_WIN_MODEL=qwen3.5-27b-claude-4.6-opus-reasoning-distilled-v2`

---

## How to Resume

```bash
# Check live status
python3 ~/.openclaw/scripts/discover.py --status

# Force re-probe
python3 ~/.openclaw/scripts/discover.py --force

# Run tests
cd ~/.openclaw/scripts && python3 -m pytest tests/test_discover.py -v

# Restore from backup
python3 ~/.openclaw/scripts/discover.py --restore latest

# Install hub from repo (idempotent)
python3 setup_macos.py
```

## Out of Scope / Future Work
- orama 5-stage agent pipeline execution (crystallizer → architect → execute → refine → verify)
- ecc-sync workflow for cross-repo lesson sync
- Ollama auto-discovery (separate concern)
