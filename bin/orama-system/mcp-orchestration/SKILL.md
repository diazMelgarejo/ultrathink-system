---
name: mcp-orchestration
description: Use when setting up Claude Code MCP tools, adding Claude Skills, using Gemini as a large-context reader, dispatching parallel AI CLI agents, connecting MCP tools to OpenClaw, or routing tasks to local/OpenRouter/Codex/Gemini agents. Trigger when the user mentions Gemini MCP, ai-cli-mcp, OpenClaw MCP, SKILL.md, Claude Skills, background agents, /mcp, MCP JSON, prompt caching, OpenRouter routing, agent dispatch, or tool setup failures.
version: 2.0.0
canonical_path: orama-system/bin/orama-system/mcp-orchestration/SKILL.md
supersedes:
  - OpenClaw/MCP_ORCHESTRATION_SKILL.md
  - OpenClaw/MCP_ORCHESTRATION_SKILL_v2.md
  - ~/.claude/skills/mcp-orchestration/SKILL.md
last_updated: 2026-05-14
---

# MCP Orchestration Skill (canonical)

**Version:** 2.0.0
**Date:** 2026-05-14
**Scope:** Claude Code, Claude Desktop, OpenClaw, Gemini MCP Tool, ai-cli-mcp, OpenRouter, local ollama, custom MCP servers
**Status:** canonical. Supersedes the two root MCP_ORCHESTRATION_SKILL*.md files. Sources merged and drift removed.

> **Canonical location:** `orama-system/bin/orama-system/mcp-orchestration/SKILL.md`
> All other copies (root markdown, user-level `~/.claude/skills/mcp-orchestration/SKILL.md`) should be redirect stubs pointing here.

---

## Executive Rule

Use the right tool for the right layer. Use the cheapest agent that can succeed.

| Layer | Tool | Job |
|---|---|---|
| Main reasoning + judgment | Claude Sonnet 4.6 medium + prompt caching | Decide, edit, review, synthesize, content insertion |
| Default coding/text agent | OpenRouter free-model stack (Nemotron → MiniMax → DeepSeek → …) | Generic worker — long-context, coding, structured output |
| Large-context reading (when specified) | `gemini-mcp-tool` | Gemini-Analyzer use-cases: architecture mapping, visual diff, screenshot comparison, multi-file audit |
| Parallel workers | `ai-cli-mcp` | Run background CLI agents (Codex, Gemini, ollama) with PID tracking |
| Local-only workloads | ollama (Mac, `localhost:11434`) | Lint, format, bash scripts, local validation — free + private |
| Runtime orchestration | OpenClaw | Route tools into agent workflows, gateway, auth |
| Repeatable procedure | Claude Skill | Encode durable operating knowledge (this file) |

**Two routing rules below override the legacy "Gemini = default reader" pattern.** See §2.

---

## 1. MCP Fundamentals

MCP lets Claude and other agents call external tools through a standard tool protocol.

### Common transport

Most local MCP tools here use `stdio` — the MCP client starts the tool as a local subprocess and talks to it over stdin/stdout.

### Common config shapes

Claude Desktop and many MCP clients:

```json
{
  "mcpServers": {
    "server-name": {
      "command": "npx",
      "args": ["-y", "package-name"]
    }
  }
}
```

OpenClaw outbound MCP registry:

```json
{
  "mcp": {
    "servers": {
      "server-name": {
        "command": "npx",
        "args": ["-y", "package-name"]
      }
    }
  }
}
```

### Claude Code verification

Inside Claude Code: `/mcp`
CLI: `claude mcp list`

---

## 2. Routing strategy (READ FIRST)

### Rule 1 — Default routing: OpenRouter free-model stack

When the caller does NOT specify an agent, route to OpenRouter free models in fallback order:

```text
1. openrouter/nvidia/nemotron-3-super-120b-a12b:free   (1M ctx, agent-strong)
2. openrouter/minimax/minimax-m2.5:free                (205K, 80.2% SWE-Bench)
3. openrouter/deepseek/deepseek-v4-flash:free          (1M, fast triage)
4. openrouter/openai/gpt-oss-120b:free                 (131K, tool-use)
5. openrouter/z-ai/glm-4.5-air:free                    (131K, agentic backup)
6. openrouter/inclusionai/ling-2.6-flash:free          (262K, lightweight)
7. openrouter/openrouter/free                          (auto-router, last resort)
```

For local-machine workloads where no network is needed, prefer `ollama qwen3.5` on Mac (`localhost:11434`) FIRST. Then fall through to OpenRouter.

See `docs/OPENROUTER_FREE_MODELS.md` for the full policy and `scripts/apply-openrouter-free-defaults.sh` for applying it to `openclaw.json` configs.

### Rule 2 — Gemini-Analyzer use-case routing (when specified)

**Gemini is NOT the default reader.** Gemini has unique strengths but also access constraints (GitHub auth issues, rate limits). Reserve it for explicitly-specified "Gemini-Analyzer use-cases":

| Use-case | Why Gemini |
|----------|------------|
| **Visual diff / screenshot comparison** | 2M-token vision context, sandbox testing |
| **Whole-repo architecture mapping** | Largest single-shot context window available |
| **Multi-file stale-doc detection** | Reads entire `docs/` + `src/` in one pass |
| **Second-opinion code review of >5000-line diffs** | Pro model handles size comfortably |

For ANY OTHER reading task (single file, narrow audit, dependency scan), route to OpenRouter Nemotron 3 Super (1M ctx, free) instead.

**Call signature pattern:**

```text
# Default reader call (uses OpenRouter):
"Read @path/to/file and report X"

# Gemini-Analyzer call (explicit):
"GEMINI-ANALYZER: visual-diff between @screenshot.png and live dev server"
```

### Rule 3 — Claude Sonnet 4.6 medium for judgment + prompt caching

Reserve Claude Sonnet 4.6 (this session's main agent) for:
- Final judgment, taste calls, conflict resolution
- Reviewing worker outputs and detecting drift
- Content insertion decisions (CIDF gate)
- Writing commit messages, summaries, designs

**Prompt caching policy (Goal 2 from RC-1 plan):**

When using Claude Sonnet 4.6 via the Anthropic SDK:
- `model: claude-sonnet-4-6`
- `thinking.effort: medium`
- Set `cache_control` on **stable** system prompts, tool definitions, and context prefixes
- Sonnet 4.6 minimum cacheable prompt: **1,024 tokens** (anything smaller is not cached)
- TTL: 5 minutes default (90 minutes with `ttl: "extended"`)
- **NEVER cache** changing suffixes — timestamps, per-run user payloads, request IDs, response IDs

Example (Python SDK):

```python
import anthropic

client = anthropic.Anthropic()

response = client.messages.create(
    model="claude-sonnet-4-5",  # or claude-sonnet-4-6 when available
    max_tokens=1024,
    thinking={"type": "enabled", "budget_tokens": 8000},
    system=[
        {
            "type": "text",
            "text": LARGE_STABLE_SYSTEM_PROMPT,
            "cache_control": {"type": "ephemeral"},  # ← cache this
        }
    ],
    messages=[
        {"role": "user", "content": ephemeral_user_input}  # ← do NOT cache
    ],
)
```

Source: <https://platform.claude.com/docs/en/build-with-claude/prompt-caching>

### Rule 4 — Use ai-cli-mcp as the parallel worker pool

Use ai-cli-mcp when:
- Tasks are independent (different files, different concerns)
- Multiple models should inspect the same repo
- You need background agents with PID tracking
- You want session reuse across subtasks

Do not let worker agents commit or deploy without explicit user confirmation.

### Rule 5 — OpenClaw as the runtime router

OpenClaw routes tools into agent workflows, holds gateway/auth, registers outbound MCP servers, and keeps security/policy around agent execution.

---

## 3. Install Baseline

Use Node.js 20+ when using both Gemini MCP Tool and ai-cli-mcp.

```bash
node -v
npm -v
```

### Install Claude Code

```bash
npm install -g @anthropic-ai/claude-code
claude doctor
```

For ai-cli-mcp Claude workers, run once manually:

```bash
claude --dangerously-skip-permissions
```

This accepts prompts so background Claude subprocesses do not hang.

### Verify Claude auth (REQUIRED before dispatching Claude workers)

Before routing work to Claude, verify auth through the exact binary the orchestrator will use:

```bash
which claude
claude --version
claude auth status --text
claude -p --permission-mode dontAsk --max-budget-usd 0.25 "Reply with exactly: claude-ready"
```

If `claude -p` reports `Not logged in` after a login attempt, assume the auth flow may have been sandbox-blocked until proven otherwise. Claude's OAuth flow needs a local callback server and host credential persistence. Run login outside the sandbox or with explicit escalation:

```bash
claude auth login --claudeai
claude auth status --text
claude -p --permission-mode dontAsk --max-budget-usd 0.25 "Reply with exactly: claude-ready"
```

If login prints success but `auth status` remains false, inspect a debug log:

```bash
claude --debug --debug-file /tmp/claude-auth-debug.log auth login --claudeai
sed -n '1,120p' /tmp/claude-auth-debug.log
```

`Failed to start OAuth callback server` is a sandbox/auth-environment failure, not a normal stale session. Escalate the auth command instead of looping.

If the machine has both native and npm-global Claude installs, compare `which claude`, `claude --version`, and known full paths. Use one exact binary for login, status, and `-p` probes.

### Install Gemini CLI

```bash
npm install -g @google/gemini-cli
gemini auth login
gemini --version
```

### Install Codex CLI (optional, Codex worker support)

```bash
npm install -g @openai/codex
codex login
```

### Install ai-cli-mcp

```bash
npm install -g ai-cli-mcp
ai-cli doctor
ai-cli models
```

### Install ollama (for local-priority routing per Rule 1)

```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama pull qwen3.5:9b-nvfp4   # Mac default model
ollama serve                    # listens on localhost:11434
```

---

## 4. gemini-mcp-tool

Repository: `jamubc/gemini-mcp-tool`

### Purpose

Bridges Gemini CLI into Claude Code or other MCP clients. Used **only for Gemini-Analyzer use-cases** per §2 Rule 2.

### Claude Code setup

```bash
claude mcp add gemini-cli -- npx -y gemini-mcp-tool
```

Verify: `/mcp` → expect `gemini-cli active`

### Claude Desktop setup

Edit `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "gemini-cli": {
      "command": "npx",
      "args": ["-y", "gemini-mcp-tool"]
    }
  }
}
```

Restart Claude Desktop.

### Reader Protocol (Gemini-Analyzer mode)

1. Mark the call as Gemini-Analyzer (explicit user intent)
2. Ask Gemini a NARROW reading question with structured output
3. Ask Claude to verify the evidence
4. Let Claude decide

Good:
```text
Ask Gemini to identify stale architecture claims in @README.md and @docs/. Return file, claim, contradiction, confidence.
```

Bad:
```text
Ask Gemini to fix the repo.
```

### Model selection

| Model | Use |
|---|---|
| Gemini Pro | architecture, whole-repo reading, security review, visual diff |
| Gemini Flash | quick review, smaller files, routine docs |

### Windows / Parallels note

Use official `gemini-mcp-tool` first. A package like `gemini-mcp-tool-windows-fixed` is a local workaround only.

---

## 5. ai-cli-mcp

Repository: `mkXultra/ai-cli-mcp`

### Purpose

Runs AI CLI tools as background worker processes with PID tracking, result retrieval, waiting, killing, cleanup.

### Critical first run

Run once:

```bash
claude --dangerously-skip-permissions
codex login
gemini auth login
```

### Claude Code setup

```bash
claude mcp add ai-cli '{"name":"ai-cli","command":"npx","args":["-y","ai-cli-mcp@latest"]}'
```

### Generic MCP config

```json
{
  "mcpServers": {
    "ai-cli-mcp": {
      "command": "npx",
      "args": ["-y", "ai-cli-mcp@latest"],
      "env": {
        "MCP_CLAUDE_DEBUG": "false"
      }
    }
  }
}
```

### Core tools

| Tool | Purpose |
|---|---|
| `run` | Launch a background AI CLI process |
| `wait` | Wait for one or more PIDs |
| `peek` | Watch short live output from a running worker |
| `get_result` | Fetch result for one worker |
| `list_processes` | List tracked workers |
| `kill_process` | Stop a stuck worker |

### Parallel dispatch pattern

```text
Use ai-cli-mcp to run three workers in parallel:

1. model=sonnet
   workFolder=/absolute/path/project
   prompt="Review src/backend for risky refactors. Return findings only."

2. model=gpt-5.2-codex
   workFolder=/absolute/path/project
   prompt="Write test suggestions for src/frontend. Do not edit files."

3. model=openrouter/nvidia/nemotron-3-super-120b-a12b:free
   workFolder=/absolute/path/project
   prompt="Read the repo and find stale docs. Return file list."

Then wait for all PIDs.
Merge outputs.
Do not modify files until I approve.
```

### Worker safety

- Use absolute `workFolder`
- Avoid destructive actions
- Do not allow background agents to commit
- Require explicit user confirmation for writes, deletes, deploys, account changes
- Kill runaway PIDs
- Archive useful results into `learnings.md` only after review

---

## 6. OpenClaw Integration

### Two roles

| Role | Command | Meaning |
|---|---|---|
| OpenClaw as MCP server | `openclaw mcp serve` | Claude or Codex talks to OpenClaw |
| OpenClaw as MCP client registry | `openclaw mcp set/list/show/unset` | OpenClaw stores outbound MCP servers |

### Add ai-cli-mcp + Gemini to OpenClaw outbound registry

```bash
openclaw mcp set ai-cli-mcp '{"command":"npx","args":["-y","ai-cli-mcp@latest"],"env":{"MCP_CLAUDE_DEBUG":"false"}}'
openclaw mcp set gemini-cli '{"command":"npx","args":["-y","gemini-mcp-tool"]}'
openclaw mcp list
```

### OpenClaw model policy (uses OpenRouter free-model stack per Rule 1)

The default OpenClaw model policy points at OpenRouter free fallbacks. Apply with:

```bash
scripts/apply-openrouter-free-defaults.sh --repo-only
scripts/apply-openrouter-free-defaults.sh --apply-live   # patches ~/.openclaw/openclaw.json
```

Full config shape lives in `deployments/macbook-pro-head/openclaw/openclaw.model-policy.jsonc`. See `docs/OPENROUTER_FREE_MODELS.md`.

### OpenClaw config shape (combined)

```json
{
  "env": {
    "OPENROUTER_API_KEY": "${OPENROUTER_API_KEY}"
  },
  "mcp": {
    "servers": {
      "ai-cli-mcp": {
        "command": "npx",
        "args": ["-y", "ai-cli-mcp@latest"],
        "env": { "MCP_CLAUDE_DEBUG": "false" }
      },
      "gemini-cli": {
        "command": "npx",
        "args": ["-y", "gemini-mcp-tool"]
      }
    }
  },
  "agents": {
    "defaults": {
      "model": {
        "primary": "openrouter/nvidia/nemotron-3-super-120b-a12b:free",
        "fallbacks": ["openrouter/minimax/minimax-m2.5:free", "openrouter/openrouter/free"]
      }
    }
  }
}
```

### Dispatch rule (embed in OpenClaw instructions)

```text
Use OpenRouter free-model stack as the default agent.
Use Gemini only for Gemini-Analyzer use-cases (visual diff, whole-repo, multi-file audits).
Use ai-cli-mcp for isolated parallel work.
Never write, delete, deploy, or commit unless the user explicitly confirms YES.
After workers finish, summarize by PID and cite each worker result.
```

---

## 7. Build a New Claude Skill

### Locations

- Personal: `~/.claude/skills/<skill-name>/SKILL.md`
- Project: `.claude/skills/<skill-name>/SKILL.md`
- Repo-canonical (orama-system pattern): `bin/orama-system/<skill-name>/SKILL.md`

### Minimal template

```markdown
---
name: build-optimizer
description: Diagnoses and fixes build failures. Use when the user mentions ENOTEMPTY, npm install failures, package manager errors, macOS file locks, or failing builds.
---

# Build Optimizer

## Instructions

When fixing build failures:

1. Identify the package manager.
2. Capture the exact error.
3. Check for file locks.
4. Remove only generated folders.
5. Reinstall dependencies.
6. Run the smallest proof test.

## Safety

Do not delete source files.
Ask before deleting unknown folders.
```

### Skill discovery rule

The `description` is the trigger surface — be specific.

Good: `description: Diagnoses MCP setup issues for Claude Code, Gemini MCP Tool, ai-cli-mcp, and OpenClaw. Use when MCP servers fail, tools do not appear in /mcp, JSON parse errors occur, or background agents hang.`

Bad: `description: Helps with MCP.`

---

## 8. Custom MCP Server Skill

Use only when existing tools do not provide the needed action.

### Scaffold

```bash
mkdir my-mcp-server && cd my-mcp-server
npm init -y
npm install @modelcontextprotocol/sdk zod
mkdir -p src
```

### Minimal TypeScript server

```typescript
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";

const server = new McpServer({ name: "my-skill", version: "1.0.0" });

server.registerTool(
  "my_tool",
  {
    description: "Runs one safe custom action.",
    inputSchema: {
      action: z.string().describe("Action to perform"),
      target: z.string().optional().describe("Target resource"),
    },
  },
  async ({ action, target }) => ({
    content: [{ type: "text", text: `Executed ${action} on ${target ?? "default"}` }],
  }),
);

const transport = new StdioServerTransport();
await server.connect(transport);
```

### Register

```bash
npx tsc
claude mcp add my-skill -- node dist/index.js
```

### Security baseline

- Use allowlists
- Keep tools narrow
- Avoid broad filesystem access
- Do not pass secrets in prompts
- Use environment variables for credentials
- Require confirmation before destructive actions

---

## 9. Tool Search

Use tool search when many MCP servers or tools are configured:

```bash
ENABLE_TOOL_SEARCH=auto claude
ENABLE_TOOL_SEARCH=auto:5 claude
```

| Tool count | Setting |
|---|---|
| < 10 tools | default usually fine |
| Many tools | `ENABLE_TOOL_SEARCH=auto` |
| Proxy / custom backend | configure explicitly if supported |

---

## 10. Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| MCP server missing | Not registered or client not restarted | Run `/mcp` and `claude mcp list` |
| Gemini tool fails | Gemini CLI not authenticated | `gemini auth login` |
| Wrong Gemini package | Old guide used wrong package | Use `@google/gemini-cli` |
| ai-cli worker hangs | First-run prompt not accepted | `claude --dangerously-skip-permissions` once |
| `claude -p` says `Not logged in` after login | OAuth callback or credential persistence failed in sandbox | `claude auth login --claudeai` outside sandbox; verify `auth status` and `claude -p` |
| Claude login says success but status is false | Login metadata was written without a usable token | Capture `--debug` log; rerun auth outside sandbox |
| Multiple Claude installs | PATH/native/global mismatch | Compare `which claude`, versions, exact binaries; use one binary everywhere |
| OpenRouter free-tier rate-limit hit | 50 req/day exceeded | Fall back to local ollama, or wait |
| OpenRouter model unavailable | Provider rate limit on that specific model | Use the fallback chain in §2 Rule 1 |
| JSON parse error | Debug logs pollute stdout | Set `MCP_CLAUDE_DEBUG=false` |
| ESM import error | Old Node version | Use Node.js 20+ |
| Agent runs forever | Worker stuck | `peek`, then `kill_process` |
| Too many tools | Tool overload | Enable tool search |
| OpenClaw cannot see server | Wrong config shape | Use `openclaw mcp set` or `mcp.servers` |

### Windows UTF-8 fix

```powershell
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$env:PYTHONIOENCODING = "utf-8"
```

---

## 11. LESSONS.md Pattern

Create `learnings.md` next to this SKILL.md. Append:

```markdown
## YYYY-MM-DD: Short title

Problem:
Cause:
Fix:
Verification:
Promote to skill:
- no
```

Promotion rule:

| Repetitions | Action |
|---|---|
| 1 | Store in `learnings.md` |
| 2–3 | Add checklist item |
| 4+ | Promote into `SKILL.md` |

---

## 12. Verification Checklist

```bash
node -v
npm -v
claude doctor
claude mcp list
gemini --version
ai-cli doctor
ai-cli models
ollama list
openclaw mcp list
```

Inside Claude Code: `/mcp`

Pass criteria:
- `gemini-cli` appears (if installed) — used for Gemini-Analyzer use-cases only
- `ai-cli-mcp` appears and is active
- ollama `qwen3.5:9b-nvfp4` listed (Mac default)
- Claude CLI first-run prompt has been accepted
- ai-cli doctor detects installed CLIs
- OpenClaw lists outbound MCP servers
- `OPENROUTER_API_KEY` is set in env
- No secrets appear in logs

---

## 13. Agent Instruction Block

Use this in `CLAUDE.md`, OpenClaw instructions, or project agent docs:

```markdown
# MCP Orchestration Policy

1. Default to OpenRouter free-model stack (Nemotron → MiniMax → DeepSeek → …) for generic worker calls.
2. Use ollama (local Mac) FIRST when no network/API is required (lint, format, bash scripts).
3. Use Gemini ONLY for Gemini-Analyzer use-cases: visual diff, whole-repo architecture, multi-file stale-doc detection, large-diff code review.
4. Use Claude Sonnet 4.6 medium + prompt caching for judgment, final synthesis, taste calls, content insertion.
5. Use ai-cli-mcp only for isolated parallel work with PID tracking.
6. Use absolute workFolder paths.
7. Never let worker agents commit, deploy, delete, or change account settings without explicit confirmation.
8. Verify every MCP server with `/mcp` or matching CLI status commands.
9. Keep MCP configs minimal.
10. Prefer allowlisted tools over broad permission bypass.
11. Record repeated fixes into learnings.md.
12. Promote repeated fixes into SKILL.md only after recurrence.
```

---

## 14. Decision Table

| Need | Use |
|---|---|
| One-time direct task | Claude Code (this session) |
| Generic worker reading or coding | OpenRouter Nemotron / MiniMax (per fallback chain) |
| Local-only lint, format, bash | ollama qwen3.5 (Mac) |
| Visual diff / screenshot comparison | Gemini Pro (Gemini-Analyzer) |
| Whole-repo architecture review | Gemini Pro (Gemini-Analyzer) |
| Multi-file stale-doc detection | Gemini Pro (Gemini-Analyzer) |
| Mechanical search-replace across many files | Codex CLI via ai-cli-mcp |
| Multiple independent worker tasks in parallel | ai-cli-mcp dispatch |
| Messaging or channel-based routing | OpenClaw |
| Judgment / content insertion / final synthesis | Claude Sonnet 4.6 + prompt cache |
| Repeated procedure to encode | Claude Skill |
| Missing capability | Custom MCP server |

---

## Final Rule

MCP is a tool layer. Do not turn every workflow into an MCP problem.

For one-time tasks, act directly.
For repeated tasks, create a skill.
For external capabilities, add an MCP server.
For parallel work, use ai-cli-mcp.
For Gemini-Analyzer use-cases (visual, large-context), use Gemini.
For everything else, use OpenRouter free models or local ollama.
For judgment, use Claude Sonnet 4.6 medium with prompt caching.

---

## Appendix: Legacy file disposition

The following files are superseded by THIS canonical SKILL.md:

| Legacy path | New status |
|-------------|------------|
| `OpenClaw/MCP_ORCHESTRATION_SKILL.md` | Redirect stub — points here |
| `OpenClaw/MCP_ORCHESTRATION_SKILL_v2.md` | Redirect stub — points here |
| `OpenClaw/MCP-INSTALL-PLAN.md` | Reference companion — kept for installation procedure |
| `~/.claude/skills/mcp-orchestration/SKILL.md` | User-level mirror — keep in sync via install-skill.sh |

Update all references to point at `orama-system/bin/orama-system/mcp-orchestration/SKILL.md`.
