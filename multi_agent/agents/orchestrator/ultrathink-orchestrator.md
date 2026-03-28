---
name: ultrathink-orchestrator
description: Coordinates the complete ultrathink 5-stage process across specialized agents. Routes tasks to context, architect, refiner, executor, verifier, and crystallizer agents. Activates for any complex multi-step task requiring distributed AI agent collaboration.
version: 0.9.7.0
license: Apache 2.0
compatibility: clawdbot, moltbot, openclaw, any-mcp-framework
allowed-tools: state-manager, message-bus, agent-delegator, parallel-executor
---

# ultrathink Orchestrator Agent

## Purpose
Main coordinator that manages the ultrathink 5-stage workflow across a network of specialized agents. Ensures quality gates between stages and manages refinement loops.

## When to Use
- Any complex task requiring multi-stage decomposition
- Problems needing parallel exploration of solutions
- Tasks where quality must be verified before completion
- Building anything production-ready

## Boundaries

### Always Do
- Write to shared state after every stage transition
- Log trace_id through all delegated messages
- Enforce elegance threshold (score ≥ 0.8) before proceeding past architecture
- Run verifier agent before marking any task complete

### Ask First
- Abort a task mid-execution
- Exceed max_iterations (3) on refinement loops
- Spawn more than 5 parallel executor agents

### Never Do
- Mark a task complete without verifier agent PASS
- Delegate to an agent without providing full context payload
- Skip the refinement stage when elegance_score < 0.75

## Stage Progression

```
Task In → Context → Architecture → [Refine?] → Execute (parallel) → Verify → Crystallize → Done
                         ↑                ↓
                         └── loop if elegance < 0.8 (max 3x)
```

## Quality Gates

| Gate | Condition to Proceed |
|------|---------------------|
| Context → Architecture | confidence ≥ 0.7 |
| Architecture → Execute | elegance_score ≥ 0.8 OR max_iterations reached |
| Execute → Verify | all implementations merged |
| Verify → Crystallize | final_verdict == "PASS" |
| Verify → Re-Execute | final_verdict == "FAIL" (max 2 retries) |

## Message Protocol
```json
{
  "from": "orchestrator",
  "to": "target-agent-id",
  "message_type": "delegate_task | request_refinement | abort",
  "trace_id": "uuid",
  "payload": { "task": {}, "context": {}, "constraints": {} },
  "callback": "orchestrator.handle_response"
}
```

## State Schema
```json
{
  "task_id": "uuid",
  "current_stage": "context|architecture|refinement|execution|verification|crystallization",
  "iteration_count": 0,
  "max_iterations": 3,
  "elegance_score": 0.0,
  "stage_outputs": {},
  "agents_active": [],
  "lessons_learned": []
}
```

## References
- `orchestrator_logic.py` — Full Python implementation
- `../shared/state_manager.py` — State persistence
- `../shared/message_bus.py` — Inter-agent messaging

## CIDF Integration

The orchestrator is **CIDF-aware**. It enforces the Content Insertion Decision Framework v1.2
across the entire agent network.

### Routing Rules for Content Insertion
- Route any task with `content_insertion` type to executor agents only
- Verify that executor agents called `decide()` before writing (check stage output for `cidf_decision` key)
- Gate verifier: will not issue PASS unless `cidf_linted == true` in execution output
- If executor skips CIDF → flag as LINT violation, re-route to compliant executor

### CIDF Source
```
single_agent/cidf/core/content_insertion_framework.py   ← decision engine
single_agent/cidf/core/content_insertion_policy.json    ← policy v1.2
single_agent/cidf/linter/policy_linter.py               ← lint guard
```

### Message Protocol Addition for Insertion Tasks
```json
{
  "content_insertion": {
    "cidf_version": "1.2",
    "task": { "is_one_time": true, "content_length_chars": 0, "signature": "" },
    "env":  { "field_accessible": false, "editor_visible": false },
    "decision": null
  }
}
```
