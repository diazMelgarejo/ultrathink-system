# Roadmap: v1.2 — Hybrid Self-Improving System

Status: Active Design → Controlled Implementation

Scope:
- Perplexity-Tools (PT) = execution + orchestration layer
- orama-system (US)= cognition + learning + memory layer

Core Principle:
Less rules. Fewer changes. High signal only.
System must improve slowly, safely, and permanently.

---

# 0. System Architecture (v1.2 Target State)

PT (Execution Layer)
- Task intake (API / agents)
- Transport (HTTP + MCP fallback)
- Agent orchestration
- Stateless execution

UTS (Cognitive Layer)
- Constraints / heuristics / anti-patterns
- Proposal engine (learning)
- Evaluator (scoring)
- Memory + pruning
- Hybrid mutation system

Loop:
PT executes → UTS evaluates → UTS mutates → PT improves

---

# 1. Non-Negotiable Rules

- No uncontrolled self-modification
- All rule changes must be logged
- Max constraints: 25
- Max mutations per cycle: 1
- Prefer reuse over new rules
- HTTP transport never removed (fallback always exists)

---

# 2. Tier Structure (Reordered for v1.2)

## Tier 2 FIRST — orama-system (Cognitive Core)

PT depends on this. Do not proceed to PT upgrades until stable.

---

# 3. orama-system v1.2 (Cognitive Engine)

## 3.1 Memory System

Create:

/ultrathink/memory/
- constraints.md
- heuristics.md
- anti_patterns.md
- lessons.md
- changelog.md

/proposals/
- pending/
- approved/
- rejected/

Rules:
- append-only
- no silent edits
- git-tracked

---

## 3.2 Evaluator Engine

Implement:

evaluate(result) →
- correctness
- constraint adherence
- clarity

Score range: 0–1  
Threshold: 0.75

Trigger learning only if below threshold.

---

## 3.3 Proposal Engine

Standard format:

type: minor | major  
scope: constraints | heuristics | workflow | evaluation  

symptom:  
cause:  
proposal:  
expected_effect:  
risk_level: low | medium | high  
reversible: yes | no  

---

## 3.4 Hybrid Mutation System

Decision logic:

IF
  risk = low
  AND reversible = true
  AND non-structural
THEN
  auto-apply (fast lane)

ELSE
  queue for human review

---

## 3.5 Constraint System

Hard limits:

- max_constraints = 25
- max_new_rules_per_cycle = 1

Reject:
- duplicates
- vague rules
- conflicting rules

---

## 3.6 Pruning System

Each rule tracks:

- created_at
- usage_count
- success_rate

Prune if:
- low usage
- low success
- redundant

---

## 3.7 Lessons System (Compounding Core)

Format:

Symptom → Cause → Fix → Rule

Mandatory:
- 1 lesson per task
- stored in lessons.md

---

## 3.8 Dual-Agent Model

Builder:
- executes tasks
- proposes improvements

Critic:
- scores output
- validates proposals
- flags risk

---

# 4. Perplexity-Tools v1.2 (Execution Layer)

## 4.1 Transport Layer (unchanged principle)

Maintain:

- HTTP bridge (primary fallback)
- MCP (optional, preferred when stable)

Rule:
System must never fail if MCP breaks.

---

## 4.2 MCP Client

orchestrator/ultrathink_mcp_client.py

Responsibilities:
- spawn subprocess
- JSON-RPC communication
- detect failure modes
- fallback to HTTP

Failure triggers:
- timeout
- crash
- incomplete response

---

## 4.3 Bridge Logic

call_ultrathink_mcp_or_bridge():

- try MCP
- on ANY failure → HTTP fallback
- always return valid result

Add:

"transport": "mcp" | "http"

---

## 4.4 FastAPI Integration

- replace direct calls with unified bridge
- no logic duplication
- minimal change surface

---

## 4.5 Async Upgrade

- migrate httpx → AsyncClient
- ensure non-blocking execution

---

# 5. PT ↔ UTS Integration (New in v1.2)

## 5.1 Post-Task Hook

After every task:

PT sends → UTS:
- task
- result
- metadata

UTS returns:
- score
- optional proposal

---

## 5.2 Learning Flow

PT does NOT mutate rules directly.

UTS owns:
- evaluation
- mutation
- memory

---

## 5.3 Enforcement Injection

All agents must:

- load constraints before execution
- reject violations
- log lessons
- avoid redundant rule creation

---

# 6. Redis Coordination (Deferred but aligned)

## Optional (v1.2+)

- shared memory state
- multi-instance coordination
- pub/sub for agent sync

Not required for core loop.

---

# 7. Governance Layer

Create:

/ultrathink/governor/

Rules:
- no rule deletion without justification
- no conflicting rules allowed
- rule cap enforced strictly
- structural changes always human-gated

---

# 8. Implementation Order (Strict)

1. UTS memory system
2. Evaluator
3. Proposal engine
4. Hybrid mutation logic
5. PT MCP client
6. PT bridge integration
7. PT ↔ UTS hook
8. Dual-agent loop
9. Pruning system

---

# 9. Success Criteria (v1.2)

System is working if:

- rule count stays <25
- repeated errors drop sharply
- proposals decrease over time
- approved rules are reused frequently
- system runs without manual correction

---

# 10. Failure Modes (Watch Closely)

- rule explosion → prune harder
- noisy proposals → tighten threshold
- agent ignores constraints → fix enforcement
- overfitting rules → downgrade to heuristics

---

# 11. Future (v1.3+ direction)

- automated proposal ranking
- cross-repo shared learning
- reinforcement weighting of rules
- agent specialization evolution

---

# Final Principle

This is not a feature.

This is a system that:
- remembers
- adapts
- stabilizes
- compounds

Every change must make the next run better.
