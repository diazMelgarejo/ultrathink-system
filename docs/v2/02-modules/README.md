# 02 — Module Index

Non-kernel modules ship at their own pace. Each plugs into the kernel via the `MiniGraph` subgraph interface.

## Module registry

| Module | File | Target version | Blocking? | Status |
|--------|------|----------------|-----------|--------|
| Multi-agent network | [multi-agent-network.md](./multi-agent-network.md) | v2.0+ (non-blocking) | No | Stub |
| MCP-Optional transport | [mcp-optional-transport.md](./mcp-optional-transport.md) | v2.0+ | No | Stub |
| Redis coordination | [redis-coordination.md](./redis-coordination.md) | v2.0+ | No | Stub |
| Self-improve evaluator | [self-improve-evaluator.md](./self-improve-evaluator.md) | v2.5 consideration | No | Stub |
| RAG + memory | [rag-and-memory.md](./rag-and-memory.md) | v2.0+ | No | Stub |
| Lessons + SKILL.md tooling | [lessons-and-skill-authoring.md](./lessons-and-skill-authoring.md) | v2.0+ | No | Stub |
| Public Plugin API | [plugin-api-public.md](./plugin-api-public.md) | v2.1 | No | Stub |

## Plug-in contract

Every module ships as a `MiniGraph` subgraph exposed via `perpetua_core.graph.subgraphs.as_node()`:

```python
from perpetua_core.graph.subgraphs import as_node
from perpetua_core.graph.engine import MiniGraph

multi_agent_sg = as_node(build_multi_agent_subgraph())

app_graph = MiniGraph()
app_graph.add_node("multi_agent", multi_agent_sg)
```

Non-kernel modules MUST NOT be imported by the kernel (`perpetua_core`). They import the kernel; never the reverse.
