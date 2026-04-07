# SKILL.md Architecture Guide
**Reference Document for ultrathink-system-skill**
**Source**: Derived from "The Architectural Optimization of Agent Capability" technical analysis

---

## Overview

A SKILL.md file is the intelligence layer of an agent skill package. It transforms a general-purpose agent into a domain-specific expert by providing specialized context, methodology, and constraints.

The architecture is deliberately simple to ensure platform agnosticism:
- One mandatory `SKILL.md` file per skill directory
- Optional `scripts/`, `references/`, and `assets/` subdirectories
- Works identically across Claude Code, Cowork, Spring AI, .NET Skills Executor, GitHub Copilot

---

## The Two Functional Regions

### 1. YAML Frontmatter (Discovery Layer)

Only the frontmatter is loaded during agent startup. This keeps discovery overhead to ~100 tokens per skill regardless of body length.

```yaml
---
name: skill-name
description: Third-person description with specific activation triggers
version: 0.9.9.0
license: Apache 2.0
compatibility: claude-code, cowork, python>=3.8
allowed-tools: bash, file-operations, web-search
---
```

| Field          | Rules                                        | Success Criterion                         |
|----------------|----------------------------------------------|-------------------------------------------|
| `name`         | 1–64 chars, lowercase, hyphens only          | Must match directory name                 |
| `description`  | 1–1024 chars, third-person, specific triggers| Trigger rate > 95% on paraphrased queries |
| `license`      | Standard license identifier                  | Legal clarity for shared registries       |
| `compatibility`| Environment/platform requirements            | Prevents failure in incompatible hosts    |
| `allowed-tools`| Space-delimited MCP tool list                | Restricts scope for security and focus    |

**Critical**: The `description` is the semantic trigger. Vague descriptions like "Database tools" fail. Specific ones like "Executes read-only SQL queries against PostgreSQL to retrieve user records" succeed.

---

### 2. Markdown Body (Execution Layer)

The body contains procedures the agent follows when the skill activates. It should stay **under 500 lines** to avoid the "ball-of-mud" anti-pattern.

**Recommended Structure**:
```markdown
## Purpose
[1–2 sentences: what this skill does and why]

## When to Use
[Specific trigger phrases and scenarios — be exhaustive here]

## Instructions
[Step-by-step procedure. Use progressive disclosure:
 - High-level steps in the body
 - Deep details delegated to references/ folder]

## Boundaries
### Always Do
[Default behaviors — consistency anchors]
### Ask First
[Human-in-the-loop operations — where judgment is needed]
### Never Do
[Strict prohibitions — files, dirs, actions to avoid absolutely]

## Examples
[1–3 golden path examples showing ideal input/output]

## References
[Links to references/ folder for deep dives]
```

---

## Progressive Disclosure Pattern

The single most important architectural principle.

**Problem**: Loading an entire API specification into context wastes tokens on every activation.

**Solution**: Body = table of contents. Details = `references/` folder.

```
SKILL.md body (always loaded):
  "For date parsing, see references/date-formats.md"

references/date-formats.md (loaded on demand):
  [Full RFC 3339 specification, examples, edge cases]
```

**Result**: Context window stays clean. Detailed reference is available when the agent specifically needs it.

---

## Calibrating Degrees of Freedom

| Tier           | When to Use                              | Instruction Style                      |
|----------------|------------------------------------------|----------------------------------------|
| **High**       | Creative, context-dependent tasks        | Heuristics and qualitative goals       |
| **Medium**     | Templated tasks with dynamic content     | Templates + pseudocode                 |
| **Low**        | Fragile, security-sensitive operations   | Exact, verbatim scripts                |

**Examples**:
- High: "Analyze code for bugs and suggest improvements" (code review)
- Medium: "Use this PRD template to generate a requirements document" (documentation)
- Low: "Execute this exact migration script verbatim" (database migration)

---

## Boundary Engineering

The three-tier hierarchy that prevents agent overreach:

```markdown
## Boundaries

### Always Do
- Follow Conventional Commit standards for all commits
- Create tasks/todo.md before implementing anything non-trivial
- Verify programmatically, never visually only

### Ask First
- Modifying any configuration file in config/
- Deleting files or directories
- Publishing or deploying to any environment
- Making changes that affect more than 5 files

### Never Do
- Modify files in vendor/, node_modules/, or .git/
- Hardcode secrets, API keys, or credentials
- Mark a task complete without running its tests
- Execute commands with sudo without explicit user approval
```

**Why this matters**: Agents default to comprehensive task completion. Explicit boundaries prevent the 2 AM "it deleted the wrong directory" incident.

---

## The 6Cs of Qualitative Success

Every production-grade skill must score well on:

1. **Clarity** — Instructions are unambiguous; no two interpretations possible
2. **Completeness** — All edge cases and failure modes addressed
3. **Conciseness** — Every sentence earns its tokens
4. **Consistency** — Same term used for same concept throughout (never mix "endpoint", "URL", "route")
5. **Correctness** — Instructions produce correct outputs when followed exactly
6. **Context** — Instructions make sense without external knowledge

---

## Quantitative Success Metrics

| Metric                    | Target  | Measurement Method                              |
|---------------------------|---------|-------------------------------------------------|
| Token ROI                 | > 10:1  | Output value tokens / instruction tokens        |
| Trigger Accuracy          | > 95%   | % of relevant queries that activate skill       |
| Boundary Violations       | 0       | Count of "Never Do" rules broken per 100 runs   |
| Execution Safety          | 100%    | Tasks verified before marked complete           |
| Repeat Mistake Rate       | < 5%    | Same mistake pattern appearing across sessions  |

---

## Anti-Patterns to Avoid

| Anti-Pattern          | Description                                     | Fix                                          |
|-----------------------|-------------------------------------------------|----------------------------------------------|
| Ball of Mud           | SKILL.md > 500 lines with no structure          | Progressive disclosure to references/        |
| Vague Description     | "Helps with data things"                        | Specific triggers: "Validates LSEG equity data" |
| Missing Boundaries    | No "Never Do" section                           | Always include explicit prohibitions         |
| Visual Verification   | "Check if it looks right"                       | Programmatic verification always             |
| No Examples           | Instructions without golden path demos          | Add at least 1 complete input→output example |
| Duplicate Instructions| Same rule stated twice with slightly different wording | Single source of truth               |

---

## File Naming Conventions

```
skill-directory-name/          # Matches 'name' field in frontmatter
├── SKILL.md                   # Always uppercase, always .md
├── references/
│   ├── kebab-case-names.md    # Lowercase, hyphens
│   └── api-reference.md
├── scripts/
│   ├── snake_case_names.py    # Python: snake_case
│   └── kebab-case-names.sh    # Bash: kebab-case
└── templates/
    └── kebab-case-template.md
```

---

## Real-World Skill Patterns

### Pattern 1: Research & Synthesis Skill
```yaml
description: Synthesizes technical documentation from multiple sources into
  structured markdown reports. Activates for "research X", "compare X and Y",
  "summarize the docs for", "what does the spec say about".
```

### Pattern 2: Code Quality Skill
```yaml
description: Reviews Python code for bugs, performance issues, and style
  violations. Activates for "review this code", "find bugs in", "optimize this
  function", "does this follow best practices".
```

### Pattern 3: Data Validation Skill
```yaml
description: Validates structured data (JSON, CSV, YAML) against schemas and
  business rules. Returns PASS/WARNING/FAIL reports. Activates for "validate
  this data", "check if this JSON is valid", "does this conform to the schema".
```

---

## Integration Notes for OpenClaw / Clawdbot / MoltBot

Skills in multi-agent environments follow the same standard with one addition: the `allowed-tools` field becomes critical for sandboxing.

```yaml
allowed-tools: bash read-only-filesystem web-search
# NOT: bash write-filesystem delete-files sudo
```

For OpenClaw lab automation (LAN-first, WhatsApp-controlled), skills should:
- Default to sandbox mode (no silent escalation)
- Require explicit approval for any destructive action
- Log all tool calls to the shared state manager
- Return structured JSON results for orchestrator parsing

---

*See also: `references/ultrathink-5-stages.md` for the methodology this skill architecture serves.*
