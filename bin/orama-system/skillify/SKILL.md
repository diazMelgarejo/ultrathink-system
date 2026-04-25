---
name: skillify
description: >-
  Interactive skill creator for orama-system, raw Claude Code, and gstack.
  Creates a new skill folder with SKILL.md, frontmatter, boundaries, examples,
  and harness registration — by asking you questions, then writing the files.
  Activates when asked to: create a skill, new skill, add a sub-skill, /skillify,
  build a new tool as a skill, make a skill, install a skill.
  Supports targets: raw-claude, orama-system sub-skill, gstack global skill, all.
version: 1.0.0
license: Apache 2.0
compatibility: claude-code, gstack
parent_skill: orama-system
triggers:
  - create a skill
  - new skill
  - /skillify
  - add sub-skill
  - build a skill
  - make a skill
  - install a skill
allowed-tools: bash, file-operations, AskUserQuestion
---

# skillify — Interactive Skill Creator

> Run from the repo root (`/path/to/orama-system/`) so relative sub-skill paths
> resolve correctly.

Creates a complete, production-grade skill from scratch — no copy-pasting, no
guessing the frontmatter format. You answer questions; skillify writes the files
and wires up registration.

Spec reference: [`references/skill-architecture-guide.md`](../references/skill-architecture-guide.md)

---

## When to Use

Use skillify when you need a new:
- **orama-system sub-skill** — lives in `bin/orama-system/<name>/`, registered in the mother skill
- **gstack global skill** — lives in `~/.claude/skills/<name>/`, invokable as `/<name>` anywhere
- **raw Claude Code skill** — a standalone `SKILL.md` that can be loaded with `/skill path/SKILL.md`

Do NOT use skillify to edit existing skills. Use it to create new ones.

---

## Step 0: Optional gstack Preamble

If gstack is installed, run its update check and analytics preamble:

```bash
if [ -x ~/.claude/skills/gstack/bin/gstack-update-check ]; then
  _UPD=$(~/.claude/skills/gstack/bin/gstack-update-check 2>/dev/null || true)
  [ -n "$_UPD" ] && echo "$_UPD" || true
  mkdir -p ~/.gstack/sessions
  touch ~/.gstack/sessions/"$PPID"
  _TEL=$(~/.claude/skills/gstack/bin/gstack-config get telemetry 2>/dev/null || echo "off")
  _SESSION_ID="$$-$(date +%s)"
  echo "GSTACK_AVAILABLE: true"
else
  echo "GSTACK_AVAILABLE: false"
fi
```

If `GSTACK_AVAILABLE: false`, skip all gstack-specific steps (Step 0, telemetry at end).
All other steps work identically without gstack.

---

## Step 1: D1 — Skill Identity

Ask via AskUserQuestion:

> **D1 — What are we building?**
>
> ELI10: A skill is a markdown file that turns a general-purpose AI into a specialist.
> The name becomes the directory and the `/command`. The purpose goes into the `description`
> field — that's what Claude uses to decide when to activate the skill automatically.
>
> Stakes if we pick wrong: a vague name or description means the skill never fires on its own,
> and you'll have to invoke it manually every time.
>
> Recommendation: Be specific. "gstack-integration" beats "tooling". "Creates SQL migration
> files from a plain-English schema change description" beats "database helper".

Questions to ask (two separate AskUserQuestion calls if needed):
1. Skill name (kebab-case, matches directory name): e.g. `sql-migrator`, `pr-triage`
2. One-sentence purpose (third-person, specific, includes trigger phrases): e.g.
   "Generates SQL migration files from plain-English schema change descriptions.
   Activates for: generate migration, schema change, add column, rename table."

Validate: name is lowercase, kebab-case only, 1-64 chars. If not, re-prompt once.

---

## Step 2: D2 — Target Context

Ask via AskUserQuestion:

> **D2 — Where should this skill live?**
>
> ELI10: Three possible homes. orama-system sub-skill = lives in this repo, loaded
> when the mother skill loads. gstack global skill = lives in your home dir, invokable
> from any project. Raw Claude = a plain SKILL.md file you load manually. You can target
> all three with one creation run.
>
> Stakes if we pick wrong: wrong home means the skill is invisible in the context you
> actually use it in.

Options:
- A) **orama-system sub-skill** — `bin/orama-system/<name>/SKILL.md`, registered in mother skill
- B) **gstack global skill** — `~/.claude/skills/<name>/SKILL.md`, invokable as `/<name>` anywhere
- C) **raw Claude Code** — custom path you specify, loaded manually with `/skill path`
- D) **all three** — write orama-system + gstack versions simultaneously

---

## Step 3: D3 — Triggers

Ask via AskUserQuestion (free-text answer):

> **D3 — What phrases should activate this skill?**
>
> ELI10: Triggers are the phrases Claude pattern-matches against to decide whether to
> load this skill. Think: what would you actually type when you need this skill? Include
> both formal names and casual phrases.
>
> Stakes: too few triggers → skill is invisible. Too vague → skill fires when it shouldn't.
>
> Example: "generate migration, schema change, add column, rename table, drop column,
> create index, alter table"

Collect as comma-separated list. Parse into a YAML `triggers:` list.

---

## Step 4: D4 — Boundaries

Ask via AskUserQuestion:

> **D4 — What should this skill always do, ask before doing, and never do?**
>
> ELI10: Boundaries are the guardrails. "Always" = defaults the skill follows every run.
> "Ask first" = actions that need a human decision (destructive, expensive, irreversible).
> "Never" = hard prohibitions.
>
> Stakes: missing boundaries leads to the "it deleted the wrong thing" 2am incident.

Present three preset options + custom:
- A) **Conservative** — Always: verify before done. Ask: any file write, any delete, any external call. Never: modify files outside the skill's target directory.
- B) **Standard** — Always: verify before done, follow CIDF for content insertion. Ask: destructive operations, deploys. Never: hardcode secrets, skip verification.
- C) **Permissive** — Always: verify before done. Ask: irreversible operations only. Never: hardcode secrets.
- D) **Custom** — I'll specify each boundary manually.

---

## Step 5: D5 — Preview and Confirm

Generate the complete frontmatter based on D1-D4 answers.

**For orama-system target:**
```yaml
---
name: <name>
description: >-
  <purpose>. Activates for: <triggers as comma list>.
version: 1.0.0
license: Apache 2.0
compatibility: claude-code
parent_skill: orama-system
triggers:
  <triggers as yaml list>
allowed-tools: bash, file-operations
---
```

**For gstack target, add:**
```yaml
preamble-tier: 1
```

Show the full preview. Ask:

> **D5 — Does this look right?**
>
> Options: A) Yes, create it. B) Edit the description. C) Edit the triggers. D) Start over.

---

## Step 6: Write the Skill Files

### Clobber guard (always run first)

```bash
TARGET_DIR="bin/orama-system/<name>"   # or ~/.claude/skills/<name> for gstack
if [ -d "$TARGET_DIR" ]; then
  echo "SKILL_EXISTS: $TARGET_DIR already exists"
  ls "$TARGET_DIR"
else
  echo "SKILL_EXISTS: false"
fi
```

If `SKILL_EXISTS: true` — ask via AskUserQuestion:
> "Directory `<name>` already exists. Overwrite, merge (add missing files only), or cancel?"
> Options: A) Overwrite, B) Merge (skip existing files), C) Cancel

If cancel: STOP with `STATUS: BLOCKED — user cancelled, existing skill preserved`.

### Write SKILL.md

Use the Write tool to create `<target_dir>/SKILL.md`.

Structure of the body (following `references/skill-architecture-guide.md`):

```markdown
# <Name> — <one-line tagline>

## Purpose
<1-2 sentences: what it does and why>

## When to Use
<Specific trigger phrases and scenarios>

## Instructions

### Step 1: <first major action>
<details>

### Step 2: <second major action>
<details>

## Boundaries

### Always Do
<from D4>

### Ask First
<from D4>

### Never Do
<from D4>

## Examples

### Example 1: <golden path label>
Input: `<example invocation>`
Output: `<expected result>`

## References
- [`skill-architecture-guide.md`](../references/skill-architecture-guide.md) — frontmatter spec, 6Cs, anti-patterns
```

For gstack target: also write a `SKILL.md.tmpl` stub:
```markdown
<!-- SKILL.md.tmpl — edit this, then run: bun run gen:skill-docs -->
<!-- This is the source template. SKILL.md is auto-generated. -->
<copy of SKILL.md body without the auto-generation comment>
```

---

## Step 7: Register in Mother Skill (orama-system targets only)

Read `bin/orama-system/SKILL.md`. Locate the `sub_skills:` block.

Check if `<name>/SKILL.md` is already listed:
```bash
grep -n "<name>/SKILL.md" bin/orama-system/SKILL.md
```

If already present: skip with note "already registered".

If not present: use the Edit tool to append to the `sub_skills:` block:
```yaml
  - path: <name>/SKILL.md
    trigger: "<comma-separated triggers from D3>"
```

---

## Step 8: Update CLAUDE.md Pointer (orama-system targets only)

First, check if CLAUDE.md already has a pointer to this skill:
```bash
grep -n "<name>" CLAUDE.md
```

If found: skip with note "CLAUDE.md already references this skill".

If not found, apply CIDF decide() — use the simplest method:
- Locate `## 9. gstack` section
- Confirm with AskUserQuestion before any write:

  > **CIDF Gate — CLAUDE.md update**
  >
  > I'll add one line to CLAUDE.md §9 pointing to `bin/orama-system/<name>/SKILL.md`.
  > CLAUDE.md is an invariant file — I want to confirm before touching it.
  >
  > Preview: `- Create skills: \`/skill bin/orama-system/<name>/SKILL.md\``
  >
  > Options: A) Add it. B) Skip — I'll add it manually.

If approved: use the Edit tool to insert the line into §9.

---

## Step 9: 6Cs Validation

Read `references/skill-architecture-guide.md`. Check the created SKILL.md against each criterion:

| C | Check | Pass condition |
|---|-------|----------------|
| Clarity | Instructions are unambiguous | No "it depends" without a decision rule |
| Completeness | Edge cases and failure modes addressed | Boundaries section has all three tiers |
| Conciseness | Every sentence earns its tokens | No section repeats another |
| Consistency | Same term used for same concept | No synonym drift |
| Correctness | Instructions produce correct output | Step sequence is executable |
| Context | Instructions make sense standalone | No unexplained jargon |

Report any failing Cs. If any fail: offer to fix inline or note for manual follow-up.

---

## Step 10: Summary

Report:

```
STATUS: DONE

Created:
  <target_dir>/SKILL.md           ← main skill file
  <target_dir>/SKILL.md.tmpl      ← template stub (gstack targets only)

Registered:
  bin/orama-system/SKILL.md       ← sub_skills: entry added (orama targets)
  CLAUDE.md §9                    ← pointer added (orama targets, if confirmed)

6Cs: <PASS / PASS_WITH_NOTES — list any Cs to revisit>

To invoke this skill:
  /skill bin/orama-system/<name>/SKILL.md          (orama-system)
  /skill ~/.claude/skills/<name>/SKILL.md           (gstack global)
  /<name>                                           (if registered in gstack)
```

---

## Telemetry (gstack only — skip if GSTACK_AVAILABLE: false)

```bash
if [ -x ~/.claude/skills/gstack/bin/gstack-timeline-log ]; then
  _TEL_END=$(date +%s)
  ~/.claude/skills/gstack/bin/gstack-timeline-log \
    '{"skill":"skillify","event":"completed","outcome":"success","session":"'"$_SESSION_ID"'"}' \
    2>/dev/null || true
fi
```

---

## Boundaries

### Always Do
- Run clobber guard before any write
- Run CIDF confirm gate before writing to CLAUDE.md
- Validate skill name is kebab-case before creating the directory
- Report 6Cs result before declaring DONE

### Ask First
- Overwriting an existing skill directory
- Writing to CLAUDE.md
- Registering in the mother skill (if the file was already present)

### Never Do
- Write to any file outside the target skill directory, `bin/orama-system/SKILL.md`, and `CLAUDE.md`
- Create documentation files (README.md, CHANGELOG.md) unless explicitly requested
- Source or execute any `.md` file as a shell script
- Skip the clobber guard
