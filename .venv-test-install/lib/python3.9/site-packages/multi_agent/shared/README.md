# Shared Utilities

> **Architecture Note:** ultrathink-system is stateless by design. The Redis backend option in these shared modules is provided for compatibility with future Perplexity-Tools distributed deployments (v1.1+). For MVP, use the default in-memory backend.

Core shared modules used by all ultrathink agents.

## Files

| File | Purpose |
|------|---------|
| `ultrathink_core.py` | Data types, enums, constants — single source of truth |
| `state_manager.py` | Cross-agent state persistence (memory/Redis/MCP) |
| `message_bus.py` | Async pub/sub messaging between agents |

## Backends

### Development (default)
```python
state = StateManager()           # in-memory
bus   = MessageBus()             # in-memory queues
```

### Production (Redis)
```python
state = StateManager(backend="redis", host="redis", port=6379)
bus   = MessageBus(backend="redis",   host="redis", port=6379)
```

### OpenClaw / MCP Native
```python
state = StateManager(backend="mcp", service_url="http://localhost:9000/state")
bus   = MessageBus(backend="mcp",   service_url="http://localhost:9000/messages")
```

## Install Dependencies
```bash
pip install redis asyncio dataclasses   # production
# or just: pip install redis
```
