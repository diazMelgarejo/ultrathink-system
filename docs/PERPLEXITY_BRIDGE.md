# Perplexity-Tools Bridge for UltraThink System

## Version 0.9.7.0

## Current Contract

This checkout treats the MCP server as the canonical integration surface between
**Perplexity-Tools** and **ultrathink-system**.

- `Perplexity-Tools` remains the top-level orchestrator and selects ultrathink
  behavior through `task_type` routing.
- `ultrathink-system` exposes the current bridge through
  `multi_agent/mcp_servers/ultrathink_orchestration_server.py`.
- The live MCP tool surface is:
  - `ultrathink_solve`
  - `ultrathink_delegate`
  - `ultrathink_status`
  - `ultrathink_lessons`

## MCP-First Flow

`Perplexity-Tools` reaches the local ultrathink reasoning layer by choosing
local-only route types such as `deep_reasoning` and `code_analysis`.

- `reasoning_depth` is not a field on `Perplexity-Tools` `OrchestrateRequest`.
- `privacy_critical` is not a live `Perplexity-Tools` request field in this
  checkout.
- Privacy isolation is currently structural: the ultrathink routes require
  `ultrathink_available` and do not include cloud or online model roles.

The practical current mapping is:

| Perplexity-Tools decision | Current bridge effect |
|---|---|
| `task_type=deep_reasoning` | Use the local ultrathink reasoning path |
| `task_type=code_analysis` | Use the local ultrathink code-analysis path |
| ultrathink unavailable | Fall back to the configured local model chain |

## Hardware Note

Perplexity-Tools owns hardware-aware routing before tasks reach ultrathink.

- `mac-studio` and `win-rtx3080` profiles stay on the PT side.
- ultrathink remains the hardware-agnostic local reasoning layer.
- The implemented HTTP backup bridge accepts `model_hint`, but PT still owns
  the hardware-routing decision that produces that hint.

## Current MCP Runtime

Run the current in-repo bridge with:

```bash
cd ultrathink-system
python multi_agent/mcp_servers/ultrathink_orchestration_server.py
```

The MCP server publishes the tool schemas defined in `TOOL_SCHEMAS` and is the
current source of truth for bridge behavior in this repository.

## HTTP Backup Status

The HTTP `/ultrathink` path is now implemented in this repo checkout as a
backup compatibility bridge via `api_server.py`.

- It is implemented in-repo.
- It is not the current primary contract.
- MCP remains the source of truth; the HTTP bridge must stay semantically aligned
  with MCP through shared mapping helpers and tests.

The exact contract mapping is:

| MCP `optimize_for` | HTTP `reasoning_depth` |
|---|---|
| `reliability` | `ultra` |
| `creativity` | `deep` |
| `speed` | `standard` |

The backup HTTP bridge also accepts `model_hint` for compatibility, but PT
hardware routing remains owned by `Perplexity-Tools`.

If neither `reasoning_depth` nor `optimize_for` is supplied, the backup server
keeps the legacy HTTP default of `reasoning_depth=standard` for compatibility
with existing direct HTTP callers.

## Historical HTTP Design Context

Earlier drafts described an HTTP escape hatch where `Perplexity-Tools` would
call `/ultrathink` and pass `reasoning_depth`. That design now exists as an
implemented backup method rather than a future-only note.

- `reasoning_depth` belongs to the backup HTTP design, not the live PT request
  model.
- `privacy_critical` explained why sensitive tasks should stay local, but it is
  still not a live PT request field in this checkout.
- PT continues to express primary routing intent through `task_type`, while the
  backup HTTP server normalizes optional `optimize_for` into `reasoning_depth`.

## Version Compatibility

This bridge documentation assumes:

- ultrathink-system >= v0.9.7.0
- Perplexity-Tools >= v0.9.0.0
- Python >= 3.8

## Related Documentation

- Perplexity-Tools: `SKILL.md`, `README.md`
- ultrathink-system: `README.md`, `docs/api-reference.md`
- MCP runtime: `multi_agent/mcp_servers/README.md`
