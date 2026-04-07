---
name: afrp
description: Audience-First Response Protocol — mandatory pre-router gate. Classifies query type (A/B/C/D), declares scope, and calibrates abstraction level before any ultrathink stage begins. Activates before generating any non-trivial output.
version: 1.0.0
license: Apache 2.0
compatibility: claude-code, cowork, open, codex
allowed-tools: bash, file-operations
---

# Audience-First Response Protocol (AFRP)

**Mandatory pre-router gate.** Run before any non-trivial output. Never skip.

---

## The Gate

Before generating output, classify the incoming query on two axes:

### Axis 1 — Query Type

| Type | Description | Response calibration |
|------|-------------|----------------------|
| **A** | Direct factual / lookup | Concise, direct answer. No elaboration. |
| **B** | Analytical / reasoning | Structured explanation, medium depth. |
| **C** | Implementation / build | Full ultrathink 5-stage process. |
| **D** | Ambiguous / meta | Clarify scope before proceeding. |

### Axis 2 — Audience Level

| Level | Signals | Calibration |
|-------|---------|-------------|
| Novice | "explain", "what is", "how do I" | Plain language, analogies, step-by-step |
| Practitioner | domain vocabulary, specific tools | Technical precision, skip basics |
| Expert | edge cases, architecture, tradeoffs | Peer-level depth, no hand-holding |

---

## Protocol Steps

```
1. READ the query fully before classifying
2. CLASSIFY: Type (A/B/C/D) × Level (Novice/Practitioner/Expert)
3. DECLARE scope: "This is a Type C / Practitioner query. Applying ultrathink MODE 2."
4. CALIBRATE output format and depth
5. PROCEED with the appropriate ultrathink mode
```

---

## Type × Mode Mapping

| Query Type | ultrathink Mode | When |
|-----------|----------------|------|
| A | MODE 1 (inline, no plan) | Simple lookup, 1-2 steps |
| B | MODE 1–2 | Analysis, explanation |
| C (small) | MODE 2 (5-stage, subagents) | Build task, 3-7 steps |
| C (large) | MODE 3 (full 7-agent network) | 8+ steps, parallel modules |
| D | Clarify first, then reclassify | Ambiguous scope |

---

## Scope Declaration Format

```
AFRP Gate: Type [A/B/C/D] | Level [Novice/Practitioner/Expert] | Mode [1/2/3]
Scope: [one sentence describing what will be done]
```

**Example**:
```
AFRP Gate: Type C | Level Practitioner | Mode 2
Scope: Implement CIDF-compliant content insertion for the form submission flow.
```

---

## Boundaries

### Always Do
- Run AFRP gate before any Type B, C, or D response
- State the gate result explicitly when using Mode 2 or 3
- Re-run gate if the user clarifies a Type D query

### Ask First
- Reclassifying from C to D (means the task is ambiguous — confirm with user)

### Never Do
- Skip the gate for complex or audience-dependent queries
- Proceed with Mode 3 without declaring it explicitly
- Assume expert level without signals confirming it

---

## Integration

AFRP is the first step in `single_agent/SKILL.md` Mode Router.
It runs before the complexity signals are evaluated.
The router is compatible with Perplexity-Tools via the current bridge, OR via the implemented backup HTTP `/ultrathink` path.

```
Query arrives → AFRP Gate → Mode Router → MODE 1 / 2 / 3
```

*See `single_agent/SKILL.md` for the full execution mode router.*
