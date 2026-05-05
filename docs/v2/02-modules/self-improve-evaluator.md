# Module: Self-Improve Evaluator

> Status: stub — ex-v1.2 roadmap, considered for v2.5

## What it does

The hybrid self-improving system from v1.2 roadmap: Evaluator (scores outputs on correctness, constraint adherence, clarity), Proposal Engine (proposes mutations), Mutation Engine (auto-applies low-risk changes; queues high-risk for human review).

## Relationship to v2.5

- MAESTRO Layer 1 (goal alignment) and SWARM risk scoring both inform which proposals are auto-applied vs. queued
- HITL interrupts (kernel primitive) serve as the human-approval mechanism for high-risk mutations
- `GossipBus` audit trail enables evaluator to replay prior sessions for scoring

## v2.5 design sketch

```
Graph node: evaluator → scores PerpetuaState output
Graph node: proposer → if score < threshold, generates proposal
Graph node: mutator → if low-risk, applies; if high-risk, raises Interrupt
Human resolves Interrupt → oramasys resumes from checkpoint
```

## Non-blocking rationale

The self-improve loop is a meta-layer on top of the kernel. The kernel doesn't need to know it exists. Evaluator/proposer/mutator are just `MiniGraph` nodes in a "meta-graph" that wraps the primary task graph.
