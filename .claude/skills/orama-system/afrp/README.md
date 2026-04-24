# AFRP — Audience-First Response Protocol

**Version:** 0.9.9.0
**Status:** Active — mandatory pre-router gate for orama-system

## Quick Start

AFRP is the first skill loaded in the ultrathink processing chain. It runs before the Execution Mode Router, before CIDF, and before any agent bifurcation.

```
Task → AFRP gate → Execution Mode Router → Mode 1/2/3 → CIDF (on insertion)
```

## Package Structure

```
afrp/
├── SKILL.md          ← Main skill file (discovery + full 7-step protocol)
├── failure-modes.md  ← Extended failure mode taxonomy with recovery procedures
└── README.md         ← This file
```

## When to Load

- **Always** on non-trivial queries before the Execution Mode Router fires
- **Explicitly** when queries contain: "write for," "guidance for," "framework for," "how should [group]," "develop this for," or any third-party audience indicator
- **Cross-agent** when Perplexity-Tools delegates to ultrathink via the current MCP bridge, or via the implemented backup HTTP `/ultrathink` path

## Core Principle

> "Point it at clear intent and it accelerates you. Point it at ambiguity and it scales the ambiguity."

AFRP is the operational implementation of the Amplifier Principle. It ensures intent is clear before any AI acceleration begins.

## Related Documents

| Document | Purpose |
|----------|---------|
| [`../SKILL.md`](../SKILL.md) | Parent skill — Execution Mode Router, 5-stage methodology |
| [`../cidf/SKILL.md`](../cidf/SKILL.md) | Content insertion decisions (runs after AFRP) |
| [`../references/amplifier-principle.md`](../references/amplifier-principle.md) | Foundational philosophy |
