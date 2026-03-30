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
- If PT restores a dedicated HTTP bridge later, model or hardware hints must be
  documented and tested in-repo before they become part of the active contract.

## Current MCP Runtime

Run the current in-repo bridge with:

```bash
cd ultrathink-system
python multi_agent/mcp_servers/ultrathink_orchestration_server.py
```

The MCP server publishes the tool schemas defined in `TOOL_SCHEMAS` and is the
current source of truth for bridge behavior in this repository.

## HTTP Backup Status

The HTTP `/ultrathink` path is retained as a future backup reference only.

- It is not implemented in this repo checkout.
- It is not the current primary contract.
- Any future HTTP bridge restoration must add an in-repo server, tests, and a
  documentation sync pass before it can be treated as active again.

TODO for future integration syncs:

- Add the HTTP server implementation to this repo if the backup path is revived.
- Add request/response tests that prove the HTTP bridge matches the MCP
  semantics.
- Document any mapping between HTTP `reasoning_depth` and MCP `optimize_for`.
- Document any PT hardware hints or model hints that become part of the HTTP
  request contract.

## Historical HTTP Design Context

Earlier drafts described an HTTP escape hatch where `Perplexity-Tools` would
call `/ultrathink` and pass `reasoning_depth`. That design is retained as
historical context only.

- `reasoning_depth` belongs to that HTTP design, not the live PT request model.
- `privacy_critical` explained why sensitive tasks should stay local, but it was
  never implemented as a live PT request field in this checkout.

If the HTTP bridge is restored later, treat it as a future backup path until
its implementation, tests, and docs are synchronized in-repo.

## Version Compatibility

This bridge documentation assumes:

- ultrathink-system >= v0.9.7.0
- Perplexity-Tools >= v0.9.0.0
- Python >= 3.8

## Related Documentation

- Perplexity-Tools: `SKILL.md`, `README.md`
- ultrathink-system: `README.md`, `docs/api-reference.md`
- MCP runtime: `multi_agent/mcp_servers/README.md`
