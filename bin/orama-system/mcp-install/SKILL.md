---
name: mcp-install
description: >-
  Use when setting up the MCP orchestration stack on a new machine or verifying
  it is installed. Covers ai-cli-mcp (parallel background workers), the OpenClaw
  MCP registry, and an optional Gemini analyzer lane when explicitly requested.
  Activates for: install mcp stack, setup gemini mcp, register ai-cli, openclaw
  mcp set, mcp orchestration setup, install mcp tools, run install-mcp-stack.sh.
version: 1.1.0
license: Apache 2.0
compatibility: claude-code
parent_skill: orama-system
triggers:
  - install mcp stack
  - setup gemini mcp
  - register ai-cli
  - openclaw mcp set
  - mcp orchestration setup
  - install mcp tools
  - run install-mcp-stack.sh
  - mcp install
allowed-tools: bash, file-operations
---

# mcp-install — MCP Orchestration Stack Installer

## Purpose

Installs the full MCP orchestration stack defined in the canonical `bin/orama-system/mcp-orchestration/SKILL.md`:
ai-cli-mcp (PID-tracked background workers), the registrations needed by Claude
Code and the OpenClaw outbound registry, and Gemini only when the analyzer lane
is explicitly requested. OpenRouter is the first-class default worker fallback
and is configured separately through the OpenRouter policy docs/scripts. Safe to
call multiple times — all steps are idempotent.

## When to Use

- Setting up the stack on a new machine for the first time
- Verifying an existing installation is complete
- Re-running after a Node.js upgrade or MCP registration gets corrupted
- Called by the orama-system mother skill to bootstrap the full environment

## Instructions

### Step 1: Locate the installer script

The canonical installer lives at:

```
bin/orama-system/scripts/install-mcp-stack.sh
```

From within the orama-system repo, run:

```bash
bash bin/orama-system/scripts/install-mcp-stack.sh
```

From any other working directory, use the absolute path:

```bash
bash "$ORAMA_ROOT/bin/orama-system/scripts/install-mcp-stack.sh"
```

Where `$ORAMA_ROOT` is the absolute path to the orama-system clone.

### Step 2: Dry-run first (recommended)

Preview what the script will do without making changes:

```bash
bash bin/orama-system/scripts/install-mcp-stack.sh --dry-run
```

Every step prints `[dry-run] <command>` instead of executing it.

### Step 3: Execute the installer

```bash
bash bin/orama-system/scripts/install-mcp-stack.sh
```

The script runs these steps in order — skipping any that are already complete:

| Step | Action | Skip condition |
|------|--------|----------------|
| 1 | Node.js ≥20 hard gate | Node <20 → fatal error |
| 2 | Install `ai-cli-mcp` globally | `ai-cli` already in PATH |
| 2b | Register `ai-cli` in Claude Code | `claude mcp list \| grep ai-cli` |
| 3 | Accept Claude first-run prompts | marker file `~/.claude/.dangerously-skip-accepted` |
| 4 | Optional Gemini analyzer lane | `--include-gemini` not passed |
| 4b | `gemini auth login` | `gemini auth check` passes |
| 4c | Register `gemini-cli` in Claude Code | `claude mcp list \| grep gemini-cli` |
| 5 | Register OpenClaw registry entries | `openclaw mcp list \| grep` each name |
| 6 | Verification summary | always runs |

### Step 4: Verify inside Claude Code

After the script completes, restart Claude Code, then run:

```
/mcp
```

Expected output: `ai-cli-mcp` listed as **active**; `gemini-cli` appears only when
`--include-gemini` was passed.

**What success looks like at each stage:**
- Step 2: `ai-cli doctor` shows installed CLIs detected
- Step 2b: `claude mcp list` shows `ai-cli`
- Step 4: `gemini --version` returns a version string only if `--include-gemini` was passed
- Step 4b: `gemini auth check` exits 0 silently only if Gemini was installed
- Step 4c: `claude mcp list` shows `gemini-cli` only when requested
- Step 5: `openclaw mcp list` shows `ai-cli-mcp` and, optionally, `gemini-cli`
- Step 6: configured tools present in summary table

Gemini is intentionally opt-in. Use the analyzer lane only when a task explicitly
requires large-context visual diff or whole-repo review. Do not treat Gemini as
the default reader for generic orchestration.

### Step 5: Force re-install (if needed)

To re-run all steps even if already installed:

```bash
bash bin/orama-system/scripts/install-mcp-stack.sh --force
```

Use `--force` after a version pin change or when debugging a silent failure.

## Post-Install: Reduce Permission Prompts

After the stack is installed, run `/fewer-permission-prompts` or manually add these
read-only rules to `.claude/settings.json` to eliminate recurring prompts from the
MCP verification steps:

```json
"permissions": {
  "allow": [
    "Bash(command -v *)",
    "Bash(claude mcp list *)",
    "Bash(~/.claude/skills/gstack/bin/gstack-config get *)",
    "Bash(openclaw mcp list *)",
    "Bash(openclaw mcp show *)"
  ]
}
```

## Rollback

If something goes wrong after installation:

```bash
npm uninstall -g @google/gemini-cli ai-cli-mcp
claude mcp remove -s user gemini-cli 2>/dev/null || claude mcp remove gemini-cli 2>/dev/null || true
claude mcp remove -s user ai-cli 2>/dev/null || claude mcp remove ai-cli 2>/dev/null || true
openclaw mcp unset gemini-cli 2>/dev/null || true
openclaw mcp unset ai-cli-mcp 2>/dev/null || true
```

## Known Failure Modes

| Symptom | Cause | Fix |
|---------|-------|-----|
| `gemini-cli` / `ai-cli` missing from `/mcp` in other projects | Registered at project scope instead of user scope | Re-run with `--force`; script now uses `-s user` |
| `ai-cli --version` prints usage text, not a version | ai-cli outputs help to stdout | Expected; script detects via `command -v`, version shown as "via npx" |
| `ai-cli worker hangs` | First-run prompt not accepted | Step 4 handles this; re-run the script |
| `JSON parse error` in ai-cli | Debug logs on stdout | `MCP_CLAUDE_DEBUG=false` already set in OpenClaw config |
| `gemini auth fails` | Not logged in | `gemini auth login` interactively |
| `ESM import error` | Node < 20 | Upgrade Node.js to ≥20 |
| `MCP server missing in /mcp` | Claude Code not restarted | Restart Claude Code after each `mcp add` |
| `openclaw: command not found` | OpenClaw not installed | Install from `~/.openclaw`; script logs a skip |
| `npm ERR! code EACCES` | Global npm permissions | Fix: `npm config set prefix ~/.npm-global` or use nvm |

## Boundaries

### Always Do
- Run `--dry-run` first when uncertain about machine state
- Check `claude mcp list` and `openclaw mcp list` before and after to confirm
- Restart Claude Code after any `mcp add` step completes

### Ask First
- Running with `--force` on a machine that is partially configured
- Uninstalling/rollback — confirm target machine before running rollback commands

### Never Do
- Hardcode API keys or auth tokens in the script or in MCP JSON configs
- Skip the Node.js ≥20 hard gate check
- Run with `--dangerously-skip-permissions` outside the first-run acceptance context (Step 4)

## Examples

### Example 1: Fresh machine setup (golden path)
```
Input: bash bin/orama-system/scripts/install-mcp-stack.sh
Output: All 7 steps complete, gemini-cli and ai-cli-mcp active in /mcp
```

### Example 2: Already installed — idempotent run
```
Input: bash bin/orama-system/scripts/install-mcp-stack.sh
Output: All steps print "→ skip:" — no changes made
```

### Example 3: Dry-run preview
```
Input: bash bin/orama-system/scripts/install-mcp-stack.sh --dry-run
Output: Each command printed as "[dry-run] <cmd>" — nothing executed
```

## References
- [`scripts/install-mcp-stack.sh`](../scripts/install-mcp-stack.sh) — the installer
- [`MCP-INSTALL-PLAN.md`](../../../../MCP-INSTALL-PLAN.md) — full autoplan review with 16 decisions
- [`skill-architecture-guide.md`](../references/skill-architecture-guide.md) — frontmatter spec
