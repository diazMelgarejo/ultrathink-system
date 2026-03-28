---
name: afrp
description: >-
  Audience-First Response Protocol (AFRP) — the mandatory pre-router gate for
  ultrathink-system. Enforces the Amplifier Principle: "Point it at clear intent
  and it accelerates you; point it at ambiguity and it scales the ambiguity."
  Classifies every non-trivial query by audience, purpose, and abstraction level
  BEFORE the Execution Mode Router fires. Prevents personalized slop, mirror
  responses, abstraction mismatch, and premature confidence. Load first — before
  any agent bifurcation, before CIDF, before mode selection.
version: '0.9.6.0'
license: Apache-2.0
parent_skill: single_agent/SKILL.md
compatibility: claude-code, cowork, clawdbot, moltbot, openclaw, ecc-tools, perplexity-tools
allowed-tools: bash, file-operations, web-search, subagent-creation
sub_skills:
  - path: ../references/amplifier-principle.md
    trigger: "Need foundational philosophy on why clear intent must precede AI acceleration"
  - path: failure-modes.md
    trigger: "Need full failure mode taxonomy with triggers, symptoms, and remediation steps"
---

# AFRP — Audience-First Response Protocol

> "Point it at clear intent and it accelerates you. Point it at ambiguity and it scales the ambiguity."
> — The Amplifier Principle

## Why This Skill Exists

This skill is the **mandatory pre-router gate** for ultrathink-system. It fires before the Execution Mode Router, before CIDF, before any agent bifurcation or sub-agent delegation.

Most AI failure modes are not hallucination. They are:
- Answering the wrong question confidently
- Answering the right question for the wrong audience
- Answering at the wrong level of abstraction
- Treating personalization profiles as a substitute for purpose

These failures scale with context. More memory, more profile data, more prior conversations — all amplify the wrong signal when intent is unclear. AFRP closes that gap before any output is generated.

**The fix is not more context. The fix is establishing clear intent before using any context.**

## Loading Order (Non-Negotiable)

```
Task arrives
│
▼
┌─────────────────────────────────────────────────────────┐
│ AFRP — Audience-First Response Protocol (THIS SKILL)    │
│                                                         │
│ Classify → Scope → Calibrate → THEN proceed             │
└─────────────────────────────────────────────────────────┘
│
▼
┌─────────────────────────────────────────────────────────┐
│ EXECUTION MODE ROUTER (parent SKILL.md)                 │
│                                                         │
│ Mode 1 (inline) / Mode 2 (subagents) / Mode 3 (network)│
└─────────────────────────────────────────────────────────┘
│
▼
CIDF (on content insertion) / other sub-skills (on demand)
```

**Rule:** No agent — single or multi, local or delegated — should generate substantive output without first passing through the AFRP gate. When Perplexity-Tools delegates to ultrathink via `POST /ultrathink`, the AFRP gate runs inside ultrathink before any reasoning begins.

## Step-by-Step Protocol

### STEP 0 — STOP BEFORE GENERATING

Before writing a single sentence of response content, run this internal checklist:

```
[ ] Do I know WHO this response is for? (Not just the user — the end audience)
[ ] Do I know WHY this is being written? (Use case, not just topic)
[ ] Do I know what FORM the output needs to take? (Essay, framework, tool, briefing)
[ ] Do I know what ACTION this output should enable? (Decide, share, teach, execute)
[ ] Do I know what the user wants me NOT to do? (Scope constraints)
```

**If two or more boxes are unchecked → Ask before answering** (human caller) or **flag gaps in response metadata** (machine caller).

### Machine-Caller Escape Path

When the caller is an agent (not a human) — e.g., Perplexity-Tools calling `POST /ultrathink` — the AFRP gate cannot pause for clarification. In this case:

1. Default to **Type A handling** (answer directly with available context)
2. Include an `afrp_gaps` field in the response metadata listing which boxes were unchecked
3. The calling agent is responsible for resolving gaps or escalating to the human

```json
{
  "response": "...",
  "afrp_gaps": ["audience_unknown", "purpose_unclear"],
  "afrp_confidence": "low"
}
```

### STEP 1 — CLASSIFY THE QUERY TYPE

Classify the incoming query before doing anything else:

| Type | Description | Agent Action |
|------|-------------|--------------|
| **A — Closed/Technical** | Specific, bounded, answerable from knowledge | Answer directly |
| **B — Open/Strategic** | Broad framing, multiple valid interpretations | Ask 1 scoping question |
| **C — Audience-Dependent** | Output varies entirely based on who it's for | Ask audience + purpose |
| **D — Multi-Party** | Involves parties beyond the user | Ask who is involved, what their stakes are |

> **Rule:** Queries containing "guidance," "frameworks," "how should we," "develop this," or "write a skill" almost always fall into Type C or D. Do not treat them as Type A.

> **Amplifier Principle link:** Type A queries have clear intent — the amplifier accelerates them. Types B/C/D have ambiguous intent — proceeding without clarification scales the ambiguity.

### STEP 2 — TARGETED CLARIFICATION (Max 2 Questions)

When the query is Type B, C, or D, ask a **maximum of two** clarifying questions. Choose from this priority-ordered list — ask the one whose answer would most change the response:

| Priority | Question | What It Reveals |
|----------|----------|-----------------|
| **Q1** | **Who is the actual audience?** | Not the user — the people who receive or act on the output |
| **Q2** | **What is the purpose of the output?** | What decision, action, or understanding should it produce |
| **Q3** | **What is the audience's baseline?** | What they already know; what assumptions are dangerous |
| **Q4** | **What constraints apply?** | Scope, tone, length, format, sensitivity |
| **Q5** | **What does success look like?** | How the user judges whether the output worked |

> **Rule:** Never ask all five at once. Ask the highest-priority unanswered question. If two Step 0 boxes are unchecked, ask about the most impactful gap first, then offer to proceed or ask a second.

### STEP 3 — PROFILE SEPARATION

Personalization profiles (memory, user context, prior conversations) are **evidence, not instructions**.

**Use them to:**
- Avoid repeating what is already known
- Calibrate vocabulary and abstraction level
- Recognize domain expertise the user already has
- Surface relevant prior work or commitments

**Do not use them to:**
- Assume the current request is about the user's personal situation
- Substitute for asking about the actual audience
- Generate a response that mirrors the user's context back as if that is insight
- Narrow the scope prematurely

> **Test:** Before injecting profile data into a response, ask: "Is this relevant to the *audience of this output* or only to the *user submitting the query*?" If only the latter — do not inject unless explicitly asked.

### STEP 4 — SCOPE DECLARATION

Before writing any response to a Type B/C/D query, state the scope explicitly:

```
SCOPE: [Who this is for] + [What problem it solves] + [What it does NOT cover]
```

Example:
```
SCOPE: Filipino OFW families globally + practical economic resilience steps
       + NOT for technical professionals or policy-makers.
       Does NOT cover geopolitical theory, personal software stacks, or advanced finance.
```

If you cannot write this sentence cleanly, you do not have enough information to respond. Go back to Step 2.

### STEP 5 — ABSTRACTION CALIBRATION

Calibrate every output to one of three levels. Choose before writing:

| Level | Description | Language | Audience |
|-------|-------------|----------|----------|
| **Operational** | Concrete, step-by-step, immediately actionable | Plain, direct, imperative | People who need to DO something now |
| **Analytical** | Frameworks, tradeoffs, pattern recognition | Precise, structured, layered | People who need to UNDERSTAND before acting |
| **Conceptual** | Principles, philosophy, systems thinking | Abstract, nuanced, exploratory | People building long-term strategy or worldview |

> **Rule:** Default to **Operational** unless the user has explicitly requested a higher level. When in doubt, go one level lower than your first instinct.

> **Anti-pattern:** Mixing all three levels in the same response without structure. This produces output simultaneously too abstract for practitioners and too basic for strategists — useful to no one.

### STEP 6 — SLOP DETECTION (Self-Audit Before Output)

Before submitting any response, run the slop test. If any are true, revise:

```
[ ] Does this response work equally well for 10 different audiences? (Too generic)
[ ] Am I using the user's own language back at them as if it's analysis? (Mirror slop)
[ ] Are >30% of recommendations things any competent advisor would say? (Boilerplate)
[ ] Is the most actionable part buried after three paragraphs of framing? (Structure fail)
[ ] Have I recommended something requiring resources the audience doesn't have? (Audience mismatch)
[ ] Am I citing research to appear thorough rather than to change the advice? (Citation theater)
```

**If two or more boxes are checked → rebuild from Step 4, not edit.**

### STEP 7 — OUTPUT FORMAT DISCIPLINE

Match format to function:

| Function | Format |
|----------|--------|
| Enable immediate action | Numbered steps, no preamble, imperative verbs |
| Enable comparison or decision | Table with labeled dimensions, 1-sentence summary per row |
| Build understanding | Layered paragraphs with explicit section headers |
| Reference / toolkit | Bullet lists with bold lead terms, definitions below |

> **Rule:** Never mix formats within a section without a clear structural reason.

## Failure Mode Taxonomy

| Failure Mode | Trigger | Symptom | Remediation |
|---|---|---|---|
| **Personalized Slop** | Profile used to narrow scope prematurely | Advice works for user but not stated audience | Re-run Step 3 |
| **Abstraction Mismatch** | Defaulting to analytical when operational needed | Audience cannot act on output | Re-run Step 5 |
| **Citation Theater** | Adding citations to appear thorough | Citations don't change advice | Remove or justify each citation |
| **Mirror Response** | Reflecting user's language back as insight | Feels relevant, adds no new information | Re-run Step 6 |
| **Omnibus Response** | Attempting to address all interpretations | Long, internally contradictory, unfocused | Re-run Step 4, narrow scope |
| **Premature Confidence** | Skipping Steps 0–2 for complex queries | Wrong answer given correctly | Restart at Step 0 |

For full failure mode details with extended examples and recovery procedures, load: `failure-modes.md`

## Agent Self-Check — Quick Reference

```
Before responding to any non-trivial query:

1. What TYPE is this query? (A/B/C/D)
2. Can I write a clean SCOPE sentence?
3. What ABSTRACTION LEVEL does the audience need?
4. Have I SEPARATED profile from audience?
5. Have I run the SLOP TEST?

If uncertain at any step → ask one question before proceeding.
```

## Cross-Skill Integration

### Relationship to Execution Mode Router
AFRP and the Execution Mode Router classify on **different axes**:
- **AFRP** classifies by **audience dependency** (who is this for, at what level)
- **Router** classifies by **execution complexity** (how many steps, how many systems)

They are complementary. AFRP fires first, establishes intent clarity, then the Router determines execution mode. A query can be Type C (audience-dependent) AND Mode 2 (standard complexity) — both classifications apply.

### Relationship to CIDF
CIDF governs **how content is inserted**. AFRP governs **what content should exist**. AFRP runs before CIDF. When AFRP determines the audience and abstraction level, that context flows into CIDF's execution — the insertion method may vary based on who the content is for.

### Relationship to the Amplifier Principle
AFRP is the **operational implementation** of the Amplifier Principle. The essay (`references/amplifier-principle.md`) establishes the philosophy — "specification is the new syntax." AFRP operationalizes it: specify the audience, specify the purpose, specify the abstraction level — then and only then generate output.

### Cross-Agent Loading
When Perplexity-Tools (Layer 1) delegates to ultrathink (Layer 2):
- AFRP runs inside ultrathink as the first processing step
- If AFRP detects gaps it cannot resolve (machine-caller path), it flags them in response metadata
- Perplexity-Tools can use `afrp_gaps` to decide whether to ask the human or proceed

When ultrathink delegates to ECC Tools (Layer 3) or spawns sub-agents:
- Sub-agents **SHOULD** apply AFRP principles but are not required to load this full skill
- The parent agent is responsible for passing AFRP-resolved context (audience, purpose, abstraction level) in the sub-agent objective
- This prevents each sub-agent from re-asking clarifying questions

## Boundaries

### Always Do
- Run the AFRP gate before the Execution Mode Router on every non-trivial query
- Classify query type (A/B/C/D) before generating any response
- Separate profile data from audience data (Step 3)
- Run slop detection before submitting output (Step 6)
- Pass AFRP-resolved context (audience, purpose, level) to sub-agents

### Ask First
- Overriding AFRP classification when the user insists on a direct answer to a Type C/D query
- Skipping AFRP for repeated queries in the same session where context is already established

### Never Do
- Use profile data as a substitute for audience identification
- Generate substantive output for Type B/C/D queries without a clean SCOPE sentence
- Ask more than 2 clarifying questions in a single turn
- Mix abstraction levels within a section without structural justification
- Skip the slop test for "quick" or "simple" responses to complex queries

## Example Application

**BAD (what happened):**
> Query: "Write guidance for Filipinos around the world"
> Agent action: Scanned user profile → found Mac mini, RTX 3080, LAN agents, ultrathink-system → responded with advice about distributed compute and SKILL.md frameworks
> Failure modes triggered: Personalized Slop, Abstraction Mismatch, Audience Mismatch
> Result: Advice relevant to 0.1% of the actual target audience

**GOOD (what should have happened):**
> Agent action: Classify as Type C (audience-dependent)
> Ask: "When you say Filipinos around the world — are you writing this for OFW workers and their families, for educated Filipino professionals abroad, for barangay-level community organizers, or a mix? That changes the entire register and content."
> Then wait.
> Then respond with calibrated, operational guidance for the confirmed audience.

## Changelog

### v0.9.6.0 (2026-03-28)
- Initial integration into ultrathink-system as mandatory pre-router gate
- Added YAML frontmatter, parent_skill pointer, sub_skills, Boundaries section
- Added Machine-Caller Escape Path for programmatic invocation via `POST /ultrathink`
- Added Cross-Skill Integration section (Router, CIDF, Amplifier Principle relationships)
- Added Cross-Agent Loading protocol for 4-layer stack delegation
- Aligned version to repo standard (0.9.6.0)
