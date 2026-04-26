---
name: gstack
description: >-
  gstack v1.12.2.0 integration sub-skill. Full routing table for web browsing,
  QA, shipping, planning reviews, design, DX audits, retros, and GBrain.
  Activates for: /browse, /qa, /ship, /review, /investigate, /design-review,
  /canary, /benchmark, /retro, gbrain, gstack skills, web browsing, QA testing,
  deploy, design review, canary monitoring, performance benchmarks.
version: 1.0.0
license: Apache 2.0
compatibility: claude-code
parent_skill: orama-system
gstack_version: "1.12.2.0"
gstack_install: "~/.claude/skills/gstack (global-git)"
---

# gstack Integration

gstack v1.12.2.0 is the agent skill framework for web browsing, planning,
review, QA, and deployment workflows. Installed globally at
`~/.claude/skills/gstack` (global-git).

## Rules

- **ALWAYS** use `/browse` for all web browsing — NEVER use `mcp__claude-in-chrome__*` tools directly
- Use `/investigate` for root-cause analysis of adapter or orchestration failures
- Use `/ship` before any `npm publish`

## Install / Update

Fresh install:
```bash
git clone --single-branch --depth 1 https://github.com/garrytan/gstack.git ~/.claude/skills/gstack && cd ~/.claude/skills/gstack && ./setup
```

Upgrade to latest:
```
/skill ~/.claude/skills/gstack/gstack-upgrade/SKILL.md
```
Or: `/gstack-upgrade`

## Available Skills

| Skill | Purpose |
|-------|---------|
| `/browse` | Headless browser for web browsing and site docs |
| `/qa` | Systematically QA test a web application and fix issues |
| `/qa-only` | Report-only QA testing |
| `/design-review` | Designer's eye QA: visual inconsistency, spacing, contrast |
| `/design-html` | Generate production-quality HTML designs |
| `/design-shotgun` | Generate multiple AI design variants |
| `/design-consultation` | Understand your product and provide design guidance |
| `/review` | Pre-landing PR review |
| `/ship` | Ship workflow: detect + merge base branch, run tests, deploy |
| `/land-and-deploy` | Land and deploy workflow |
| `/canary` | Post-deploy canary monitoring |
| `/benchmark` | Performance regression detection |
| `/office-hours` | YC Office Hours — startup or project mode |
| `/plan-ceo-review` | CEO/founder-mode plan review |
| `/plan-eng-review` | Eng manager-mode plan review |
| `/plan-design-review` | Designer's eye plan review |
| `/plan-devex-review` | Interactive developer experience plan review |
| `/autoplan` | Auto-review pipeline |
| `/devex-review` | Live developer experience audit |
| `/retro` | Weekly engineering retrospective |
| `/investigate` | Systematic debugging with root cause investigation |
| `/document-release` | Post-ship documentation update |
| `/codex` | OpenAI Codex CLI wrapper |
| `/cso` | Chief Security Officer mode |
| `/learn` | Manage project learnings |
| `/careful` | Safety guardrails for destructive commands |
| `/freeze` | Restrict file edits to a specific directory |
| `/unfreeze` | Clear the freeze boundary set by /freeze |
| `/guard` | Full safety mode: destructive command warnings |
| `/setup-browser-cookies` | Import cookies from real Chromium browser |
| `/setup-deploy` | Configure deployment settings |
| `/setup-gbrain` | Set up gbrain for this coding agent |
| `/connect-chrome` | Pair a remote AI agent with your browser |
| `/gstack-upgrade` | Upgrade gstack to the latest version |
| `/skillify` | Create a new orama-system or gstack skill interactively |

## Skill Routing

When the user's request matches a skill below, invoke it via the Skill tool.
Multi-step workflows and quality gates produce better results than ad-hoc answers.
A false positive is cheaper than a false negative.

| Signal | Invoke |
|--------|--------|
| Product ideas, "is this worth building", brainstorming | `/office-hours` |
| Strategy, scope, "think bigger", "what should we build" | `/plan-ceo-review` |
| Architecture, "does this design make sense" | `/plan-eng-review` |
| Design system, brand, "how should this look" | `/design-consultation` |
| Design review of a plan | `/plan-design-review` |
| Developer experience of a plan | `/plan-devex-review` |
| "Review everything", full review pipeline | `/autoplan` |
| Bugs, errors, "why is this broken", "this doesn't work" | `/investigate` |
| Test the site, find bugs, "does this work" | `/qa` or `/qa-only` |
| Code review, check the diff, "look at my changes" | `/review` |
| Visual polish, design audit, "this looks off" | `/design-review` |
| Developer experience audit, try onboarding | `/devex-review` |
| Ship, deploy, create a PR, "send it" | `/ship` |
| Merge + deploy + verify | `/land-and-deploy` |
| Configure deployment | `/setup-deploy` |
| Post-deploy monitoring | `/canary` |
| Update docs after shipping | `/document-release` |
| Weekly retro, "how'd we do" | `/retro` |
| Second opinion, codex review | `/codex` |
| Safety mode, careful mode, lock it down | `/careful` or `/guard` |
| Restrict edits to a directory | `/freeze` or `/unfreeze` |
| Upgrade gstack | `/gstack-upgrade` |
| Save progress, "save my work" | `/context-save` |
| Resume, restore, "where was I" | `/context-restore` |
| Security audit, OWASP, "is this secure" | `/cso` |
| Make a PDF, document, publication | `/make-pdf` |
| Launch real browser for QA | `/open-gstack-browser` |
| Import cookies for authenticated testing | `/setup-browser-cookies` |
| Performance regression, page speed, benchmarks | `/benchmark` |
| Review what gstack has learned | `/learn` |
| Tune question sensitivity | `/plan-tune` |
| Code quality dashboard | `/health` |
| Create a new skill | `/skillify` |

## GBrain Configuration

Configured by `/setup-gbrain` on 2026-04-25.

| Field | Value |
|-------|-------|
| Engine | pglite |
| Config file | `~/.gbrain/config.json` (mode 0600) |
| MCP registered | yes — user scope (`mcp__gbrain__*` tools active after Claude Code restart) |
| Memory sync | full — `github.com/diazMelgarejo/gstack-brain-lawrencecyremelgarejo` |
| Repo policy | read-write (orama-system imported, embedding running in background) |

To re-run setup or change engine: `/setup-gbrain`
