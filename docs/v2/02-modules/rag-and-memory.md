# Module: RAG + Memory

> Status: stub — deferred from v2.0 kernel

## What it does

Retrieval-Augmented Generation and persistent memory beyond the `GossipBus` event log. Enables agents to query past sessions, retrieve relevant context, and maintain long-term user/project state.

## Why deferred from kernel

RAG adds vector DB dependency (Chroma, Qdrant, or pgvector). This violates the dependency-minimal kernel principle (D4). The `GossipBus` audit log gives sufficient "memory" for kernel-level routing decisions. Semantic retrieval is an application concern.

## Design sketch

- `MemoryNode` — subgraph node that queries a vector DB for relevant past `GossipBus` events
- Plugs in at the start of the ultrathink 5-stage flow (Context stage)
- Vector DB adapter is swappable (Chroma for local, Qdrant for LAN-distributed)

## Dependencies

- Vector DB client (Chroma / Qdrant / pgvector)
- Embedding model (can route to Mac LM Studio MLX embedding endpoint)
- `perpetua_core.gossip.GossipBus` (source of text to embed)
