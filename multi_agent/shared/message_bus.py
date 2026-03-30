#!/usr/bin/env python3
"""
message_bus.py
==============
Async message bus for inter-agent communication.
Version: 0.9.9.0 | License: Apache 2.0

Supports:
- In-memory asyncio queue (development/testing)
- Redis pub/sub (production)
- MCP native messaging (Clawdbot/OpenClaw)

Usage:
    bus = MessageBus()
    await bus.publish(AgentMessage(...))
    msg = await bus.subscribe("context-agent")
"""
from __future__ import annotations
import asyncio
import json
import logging
from typing import Any, Callable, Optional, TYPE_CHECKING
from dataclasses import asdict

if TYPE_CHECKING:
    import redis.asyncio as aioredis

logger = logging.getLogger(__name__)


class MessageBus:
    """Async pub/sub message bus for the ultrathink agent network."""

    def __init__(self, backend: str = "memory", **kwargs):
        self.backend = backend
        self._queues:    dict[str, asyncio.Queue] = {}
        self._handlers:  dict[str, list[Callable]] = {}
        self._client:    Optional[Any] = None

        if backend == "redis":
            self._init_redis(**kwargs)

    def _init_redis(self, host: str = "localhost", port: int = 6379, **_):
        try:
            import redis.asyncio as aioredis
            self._client = aioredis.Redis(host=host, port=port, decode_responses=True)
            logger.info("MessageBus: Redis backend at %s:%d", host, port)
        except ImportError:
            logger.warning("redis not installed. Falling back to in-memory.")
            self.backend = "memory"

    # ── Core interface ────────────────────────────────────────────────────────

    async def publish(self, message) -> bool:
        """Publish a message to the target agent's queue."""
        try:
            target = message.to_agent
            payload = message.to_dict() if hasattr(message, "to_dict") else message

            client = self._client
            if self.backend == "redis" and client is not None:
                await client.publish(f"agent:{target}", json.dumps(payload))
            else:
                if target not in self._queues:
                    self._queues[target] = asyncio.Queue()
                await self._queues[target].put(payload)

            # Call registered handlers
            for handler in self._handlers.get(target, []):
                asyncio.create_task(handler(payload))

            logger.debug("Published to %s: %s", target, payload.get("message_type"))
            return True
        except Exception as e:
            logger.error("MessageBus.publish error: %s", e)
            return False

    async def subscribe(self, agent_id: str, timeout: float = 30.0) -> Optional[dict]:
        """Wait for a message addressed to agent_id. Returns None on timeout."""
        try:
            if agent_id not in self._queues:
                self._queues[agent_id] = asyncio.Queue()
            return await asyncio.wait_for(
                self._queues[agent_id].get(),
                timeout=timeout
            )
        except asyncio.TimeoutError:
            logger.debug("subscribe(%s): timeout after %.1fs", agent_id, timeout)
            return None
        except Exception as e:
            logger.error("MessageBus.subscribe(%s): %s", agent_id, e)
            return None

    def register_handler(self, agent_id: str, handler: Callable) -> None:
        """Register a callback handler for messages to agent_id."""
        if agent_id not in self._handlers:
            self._handlers[agent_id] = []
        self._handlers[agent_id].append(handler)
        logger.debug("Registered handler for %s", agent_id)

    async def parallel_delegate(self, tasks: list[tuple[str, dict]]) -> list[dict]:
        """
        Delegate multiple tasks to agents in parallel.
        tasks: list of (agent_id, payload) tuples
        Returns: list of results in same order as tasks
        """
        # Relative import for sibling module
        try:
            # Try absolute import first (if added to path)
            from ultrathink_core import AgentMessage, MessageType
        except ImportError:
            # Fallback to absolute path-based import or relative
            from .ultrathink_core import AgentMessage, MessageType

        futures = []
        trace_ids = []

        for agent_id, payload in tasks:
            msg = AgentMessage(
                from_agent="orchestrator",
                to_agent=agent_id,
                message_type=MessageType.DELEGATE_TASK,
                payload=payload,
            )
            await self.publish(msg)
            trace_ids.append(msg.trace_id)
            futures.append(self.subscribe(f"result:{msg.trace_id}"))

        results = await asyncio.gather(*futures, return_exceptions=True)
        # Ensure returned type is list[dict]
        return [
            r if (isinstance(r, dict) and not isinstance(r, Exception)) 
            else {"error": str(r)} for r in results
        ]

    async def close(self):
        client = self._client
        if self.backend == "redis" and client is not None:
            await client.close()
