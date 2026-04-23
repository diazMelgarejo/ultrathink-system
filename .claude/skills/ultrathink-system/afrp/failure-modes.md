# AFRP Failure Mode Taxonomy — Extended Reference

**Parent skill:** [`afrp/SKILL.md`](https://github.com/diazMelgarejo/orama-system/blob/main/bin/skills/afrp/SKILL.md)

This document provides extended examples and recovery procedures for each AFRP failure mode. Load on demand when diagnosing a response quality issue.

---

## Failure Mode 1: Personalized Slop

**Trigger:** Profile data used to narrow scope before audience is identified.

**Mechanism:** The agent scans user memory/context, finds domain-specific keywords (e.g., "distributed compute," "LAN agents," "SKILL.md frameworks"), and generates output calibrated to that profile — even when the query is about a completely different audience.

**Symptom:** Output feels relevant to the user but is useless for the stated audience. The user recognizes their own language and context mirrored back, creating an illusion of quality.

**Example:**
- Query: "Write guidance for Filipinos around the world"
- Agent finds: Mac mini, RTX 3080, orama-system, multi-agent architecture
- Output: Advice about building distributed AI systems for economic resilience
- Actual audience need: Practical steps for OFW families managing remittances

**Recovery:** Re-run Step 3 (Profile Separation). Ask: "Is this profile information relevant to the audience of this output, or only to the user submitting the query?"

---

## Failure Mode 2: Abstraction Mismatch

**Trigger:** Defaulting to Analytical or Conceptual level when the audience needs Operational.

**Mechanism:** Complex or philosophical prompts trigger the agent's tendency to match complexity with complexity. The agent produces frameworks, taxonomies, and principles when the audience needs step-by-step instructions.

**Symptom:** The audience cannot act on the output without first translating it into concrete steps. The response is intellectually interesting but operationally inert.

**Example:**
- Query: "How should small business owners protect themselves from tariffs?"
- Agent output: A framework comparing supply chain resilience theories
- Actual need: "Here are 5 things to do this week"

**Recovery:** Re-run Step 5 (Abstraction Calibration). Default to Operational. Ask: "Does this audience need to UNDERSTAND or to DO?"

---

## Failure Mode 3: Citation Theater

**Trigger:** Adding citations to appear thorough rather than because they change the advice.

**Mechanism:** The agent inserts research references, statistics, and expert quotes that decorate the response without altering its substance. Remove the citations and the advice is identical.

**Symptom:** The response looks well-researched but the citations are ornamental. They don't resolve ambiguity, challenge assumptions, or provide evidence for a contested claim.

**Test:** For each citation, ask: "If I removed this citation, would the advice change?" If no — the citation is theater.

**Recovery:** Remove or justify each citation. Every citation must earn its place by changing, qualifying, or strengthening a specific claim.

---

## Failure Mode 4: Mirror Response

**Trigger:** Reflecting the user's own language and framing back at them as if it constitutes analysis.

**Mechanism:** The agent identifies key terms and structures in the prompt, then reorganizes them into a response that feels like it "gets it" — without adding new information, new perspective, or new connections.

**Symptom:** The user reads the response and thinks "yes, that's what I said." No new insight is generated. The response validates but does not advance.

**Test:** Highlight every sentence that contains information not already present in the prompt. If less than 50% of the response is novel — it's a mirror.

**Recovery:** Re-run Step 6 (Slop Detection). Force the response to contain at least one insight, tradeoff, or recommendation the user did not already articulate.

---

## Failure Mode 5: Omnibus Response

**Trigger:** Attempting to address all possible interpretations of an ambiguous query instead of narrowing scope.

**Mechanism:** Instead of asking a clarifying question (which takes one turn), the agent hedges by covering every plausible interpretation. The result is long, internally contradictory, and unfocused.

**Symptom:** The response contains sections that contradict each other. Advice for audience A conflicts with advice for audience B, but both are presented as valid. The user must do the scoping work the agent should have done.

**Example:**
- Query: "Develop a resilience framework"
- Agent output: Section 1 (for individuals), Section 2 (for organizations), Section 3 (for governments), Section 4 (for communities) — each shallow, none actionable

**Recovery:** Re-run Step 4 (Scope Declaration). Write one clean SCOPE sentence. If you cannot — go back to Step 2 and ask.

---

## Failure Mode 6: Premature Confidence

**Trigger:** Skipping Steps 0–2 entirely for queries that appear straightforward but are actually Type B/C/D.

**Mechanism:** The agent pattern-matches the surface structure of the query to a known template and generates a confident response without checking whether the template applies. This is the most dangerous failure mode because the output looks correct.

**Symptom:** The answer is well-structured, well-cited, and completely wrong for the actual need. The user only discovers this after acting on it.

**Example:**
- Query: "Write a skill for conflict resolution"
- Agent output: A complete SKILL.md file for AI agent conflict resolution in multi-agent systems
- Actual need: A training module for HR managers on workplace conflict
- The query looked like Type A (technical, bounded) but was actually Type C (audience-dependent)

**Recovery:** Restart at Step 0. Run the full checklist. When in doubt about query type, classify UP (A→B, B→C) rather than down.

---

## Diagnostic Decision Tree

```
Response feels wrong but you can't pinpoint why?
│
├── Does it mirror the user's language? → Failure Mode 4 (Mirror)
├── Does it work for 10 different audiences? → Failure Mode 1 (Slop) or 5 (Omnibus)
├── Can the audience act on it immediately? → Failure Mode 2 (Abstraction Mismatch)
├── Remove citations — does advice change? → Failure Mode 3 (Citation Theater)
└── Was the query classified correctly? → Failure Mode 6 (Premature Confidence)
```
