#!/usr/bin/env python3
"""
state_manager.py
================
Shared state persistence for the ultrathink multi_agent network.
Version: 2.0.0 | License: Apache 2.0

Provides a simple key-value store interface that can be backed by:
- In-memory dict (development/testing)
- Redis (production, recommended)
- MCP State Service (Clawdbot/OpenClaw native)

Usage:
    state = StateManager()               # in-memory
    state = StateManager(backend="redis", host="localhost", port=6379)
    state = StateManager(backend="mcp",  service_url="...")
"""
from __future__ import annotations
from typing import Any, Optional, TYPE_CHECKING
import asyncio
import logging
import json

if TYPE_CHECKING:
    import redis.asyncio as aioredis

logger = logging.getLogger(__name__)


class StateManager:
    """
    Async key-value state store for cross-agent data sharing.

    All keys use hierarchical naming: "domain:id:field"
    Example: "task:abc123:context"
    """

    def __init__(self, backend: str = "memory", **kwargs):
        self.backend = backend
        self._store: dict[str, str] = {}
        self._client: Optional[Any] = None

        if backend == "redis":
            self._init_redis(**kwargs)
        elif backend == "mcp":
            self._init_mcp(**kwargs)
        # "memory" uses _store dict — no init needed

    def _init_redis(self, host: str = "localhost", port: int = 6379, db: int = 0, **_):
        """Initialize Redis backend. Requires: pip install redis"""
        try:
            import redis.asyncio as aioredis
            self._client = aioredis.Redis(host=host, port=port, db=db, decode_responses=True)
            logger.info("StateManager: Redis backend initialised at %s:%d", host, port)
        except ImportError:
            logger.warning("redis package not installed. Falling back to in-memory.")
            self.backend = "memory"

    def _init_mcp(self, service_url: str = "", **_):
        """Initialize MCP State Service backend. STUB — implement for your framework."""
        logger.info("StateManager: MCP backend stub. service_url=%s", service_url)

    # ── Core interface ────────────────────────────────────────────────────────

    async def get(self, key: str) -> Optional[Any]:
        """Retrieve a value by key. Returns None if not found."""
        try:
            client = self._client
            if self.backend == "redis" and client is not None:
                raw = await client.get(key)
                return json.loads(raw) if raw else None
            else:
                raw = self._store.get(key)
                return json.loads(raw) if raw else None
        except Exception as e:
            logger.error("StateManager.get(%s): %s", key, e)
            return None

    async def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> bool:
        """Store a value. Returns True on success."""
        try:
            raw = json.dumps(value)
            client = self._client
            if self.backend == "redis" and client is not None:
                if ttl_seconds:
                    await client.setex(key, ttl_seconds, raw)
                else:
                    await client.set(key, raw)
            else:
                self._store[key] = raw
            return True
        except Exception as e:
            logger.error("StateManager.set(%s): %s", key, e)
            return False

    async def delete(self, key: str) -> bool:
        """Delete a key. Returns True on success."""
        try:
            client = self._client
            if self.backend == "redis" and client is not None:
                await client.delete(key)
            else:
                self._store.pop(key, None)
            return True
        except Exception as e:
            logger.error("StateManager.delete(%s): %s", key, e)
            return False

    async def list_keys(self, prefix: str = "") -> list[str]:
        """List all keys matching a prefix."""
        try:
            client = self._client
            if self.backend == "redis" and client is not None:
                pattern = f"{prefix}*" if prefix else "*"
                return await client.keys(pattern)
            else:
                return [k for k in self._store.keys() if k.startswith(prefix)]
        except Exception as e:
            logger.error("StateManager.list_keys(%s): %s", prefix, e)
            return []

    # ── Convenience helpers ───────────────────────────────────────────────────

    async def get_task_state(self, task_id: str) -> Optional[dict]:
        return await self.get(f"task:{task_id}:state")

    async def set_task_state(self, task_id: str, state: dict) -> bool:
        return await self.set(f"task:{task_id}:state", state)

    async def get_stage_output(self, task_id: str, stage: str) -> Optional[dict]:
        return await self.get(f"task:{task_id}:stage:{stage}")

    async def set_stage_output(self, task_id: str, stage: str, output: dict) -> bool:
        return await self.set(f"task:{task_id}:stage:{stage}", output)

    async def append_lesson(self, lesson: dict) -> bool:
        existing = await self.get("lessons:all") or []
        existing.append(lesson)
        return await self.set("lessons:all", existing)

    async def get_lessons(self, domain: Optional[str] = None) -> list[dict]:
        all_lessons = await self.get("lessons:all") or []
        if domain:
            return [l for l in all_lessons if domain.lower() in l.get("applied_to", "").lower()]
        return all_lessons

    async def close(self):
        client = self._client
        if self.backend == "redis" and client is not None:
            await client.close()
