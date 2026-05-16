# OpenRouter Free-Model Policy (RC-1)

**Status:** Active default model policy as of 2026-05-14
**Source spec:** [`OpenClaw/v1/OpenRouter.md`](../../v1/OpenRouter.md)
**Canonical MCP routing:** [`bin/orama-system/mcp-orchestration/SKILL.md`](../bin/orama-system/mcp-orchestration/SKILL.md) §2
**Apply with:** `scripts/apply-openrouter-free-defaults.sh`
**Verify with:** `scripts/verify-openrouter-models.sh`

---

## What this policy is

OpenClaw and the orama-system agent network default to **OpenRouter free models** as the generic worker pool. This replaces blanket Gemini routing (which now serves "Gemini-Analyzer use-cases" only — visual diff, whole-repo, multi-file audits).

The policy is benchmark-informed and uses pinned `*:free` model IDs for deterministic behavior, with `openrouter/openrouter/free` as the auto-router fallback.

---

## Routing chain (this session's adopted order)

| # | Model | Context | Use |
|---|-------|---------|-----|
| 1 | ollama qwen3.5:9b-nvfp4 (local Mac) | local | Lint, format, bash scripts, no-network workloads |
| 2 | openrouter/nvidia/nemotron-3-super-120b-a12b:free | 1M | Primary worker — agent reasoning, long-context |
| 3 | openrouter/minimax/minimax-m2.5:free | 205K | Coding, document generation (80.2% SWE-Bench) |
| 4 | openrouter/deepseek/deepseek-v4-flash:free | 1M | Fast triage, heartbeat checks |
| 5 | openrouter/openai/gpt-oss-120b:free | 131K | Structured output, tool use |
| 6 | openrouter/z-ai/glm-4.5-air:free | 131K | Agentic backup |
| 7 | openrouter/inclusionai/ling-2.6-flash:free | 262K | Speed-focused parsing |
| 8 | openrouter/openrouter/free | varies | Auto-router, last resort |
| 9 | gemini (Pro/Flash) | 2M | **Analyzer-only backstop** — visual diff, whole-repo audit, never first-class fallback |

Models 2–8 are accessed via OpenRouter API (`OPENROUTER_API_KEY`).
Model 1 is local-only (no API cost).
Model 9 is access-constrained (GitHub auth issues per user note) — reserve for visual/large-context specialty and keep it behind the OpenRouter fallback chain.

---

## Per-agent overrides

| Agent | Primary | Why |
|-------|---------|-----|
| Frontdoor | Ling 2.6 Flash | Fast parser, messaging profile |
| LogRotator | DeepSeek V4 Flash | Fast long-context for log triage |
| Backup | Nemotron 3 Super | Long-term coherence |
| Reporter | MiniMax M2.5 | Document generation strength |
| Ops | Nemotron 3 Super | Agent-strong primary with broad fallback |

Full per-agent config: [`deployments/macbook-pro-head/openclaw/openclaw.model-policy.jsonc`](../deployments/macbook-pro-head/openclaw/openclaw.model-policy.jsonc).

---

## Free-tier rate-limit reality

- Free users: **50 requests/day**, 20 requests/minute
- PAYG users with ≥$10 credit: up to 1000 free-model requests/day, still 20 RPM
- Failed attempts can still count against quota
- For high-volume workflows: keep ollama on Mac as the first-line worker

Source: [openrouter.ai/pricing](https://openrouter.ai/pricing)

---

## Security rules (recap from OpenRouter.md §11)

Free models may have provider-specific logging. For lab/RC-1 work:

- **No secrets in prompts** — no API keys, passwords, payroll, PHI, credential dumps, private keys
- **Wrappers stay deterministic** — `LLM → structured intent → signed wrapper → strict action allowlist → JSON result`
- **Human gates preserved:**
  - dry-run default
  - `--apply` requires explicit YES
  - signed wrapper verification
  - WhatsApp allowlist
  - sandbox defaults
  - no Cron escalation

---

## Apply / verify

```bash
# Repo templates only (safe, no live changes)
scripts/apply-openrouter-free-defaults.sh --repo-only

# Patch live ~/.openclaw/openclaw.json (requires OPENROUTER_API_KEY)
scripts/apply-openrouter-free-defaults.sh --apply-live

# Verify the policy is in place and endpoints are reachable
scripts/verify-openrouter-models.sh
```

---

## CHANGELOG (this policy)

### 2026-05-14 — RC-1 adoption

- Adopted OpenRouter free-model policy from `OpenClaw/v1/OpenRouter.md`
- Added ollama qwen3.5:9b-nvfp4 as local-first priority (per Mac hard requirement in CLAUDE.md)
- Pushed Gemini to "Gemini-Analyzer use-case" routing (visual diff + whole-repo only) due to GitHub access issues
- Canonical MCP orchestration skill at `bin/orama-system/mcp-orchestration/SKILL.md` references this policy as §2 Rule 1
- Preserved LAN gateway, WhatsApp allowlist, sandbox, wrapper safety defaults
