# Module: Multi-Agent Network

> Status: stub — v1 carry-over planned for v2.0+

## What it does

Port the existing 7-agent network from `orama-system/bin/agents/` into the new architecture as a `MiniGraph` subgraph. Agents: Orchestrator, Context, Architect, Refiner, Executor ×5, Verifier, Crystallizer.

## Carry-over path

- Source: `orama-system/bin/agents/{orchestrator,context,architect,refiner,executor,verifier,crystallizer}/`
- Target: `oramasys/orama/agents/network.py` as a `MiniGraph` composition
- Each agent becomes a `MiniGraph` node; inter-agent messaging via `GossipBus`

## v1 → v2 changes

- Drop `SOUL.md` behavioral files in favor of typed `PerpetuaState` fields
- Replace ad-hoc message bus with `GossipBus` events
- HITL interrupts replace synchronous human-approval loops

## Dependencies

- `perpetua_core.graph.engine.MiniGraph`
- `perpetua_core.graph.subgraphs.as_node`
- `perpetua_core.gossip.GossipBus`

## Open items

- Whether the 7-agent topology is preserved or refactored (5-stage ultrathink maps well to 5 of the 7 agents)
- Agent registry format: YAML declarative vs. Python imperative
