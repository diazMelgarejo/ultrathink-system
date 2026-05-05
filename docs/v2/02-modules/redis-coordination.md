# Module: Redis Coordination

> Status: stub — ex-v1.1 roadmap, optional

## What it does

Replaces SQLite-based `GossipBus` with Redis pub/sub for multi-instance LAN coordination. Required only when running multiple `oramasys` instances on different machines (e.g., a Mac orchestrator + Windows executor, each running their own server).

## Decision gate

Only implement if single-instance SQLite `GossipBus` proves insufficient. SQLite handles concurrent reads fine; concurrent cross-machine writes are the trigger.

## Design sketch

- `RedisBus` implements the same `emit()` / `subscribe()` interface as `GossipBus`
- Swappable via config: `GOSSIP_BACKEND=redis` vs `GOSSIP_BACKEND=sqlite`
- Redis channel naming: `perpetua:events:{session_id}`

## Dependencies

- `redis-py` async client (`redis[asyncio]`)
- Running Redis instance (or Valkey) on LAN
