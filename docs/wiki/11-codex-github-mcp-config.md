# 11. Codex GitHub MCP Config Failure

**TL;DR:** For Codex GitHub MCP, classify transport first. The local npm GitHub MCP server is stdio,
so PAT auth belongs in `[mcp_servers.github.env]`, not `bearer_token_env_var`. GitHub's remote HTTP
MCP endpoint is a different valid shape.

---

## Root Cause

Codex failed by treating a generic auth warning as a complete config recipe. The warning suggested
`bearer_token_env_var`, but the active GitHub MCP server was a stdio subprocess. In Codex config,
`bearer_token_env_var` belongs to HTTP MCP servers, while stdio servers require `command`/`args` and
environment variables under `[mcp_servers.<name>.env]`.

The real error, `invalid transport`, was a schema problem first.

The confusion is understandable but still preventable: GitHub's own current Codex guide documents a
remote Streamable HTTP endpoint where `bearer_token_env_var` is correct. Claude's fix applied to the
local `npx @modelcontextprotocol/server-github` server, which is stdio.

## Working Fix

Local stdio GitHub MCP:

```toml
[mcp_servers.github]
transport = "stdio"
command = "npx"
args = ["-y", "@modelcontextprotocol/server-github"]

[mcp_servers.github.env]
GITHUB_PERSONAL_ACCESS_TOKEN = "${CODEX_GITHUB_PERSONAL_ACCESS_TOKEN}"
```

Remote HTTP GitHub MCP is a different transport and uses `url` plus `bearer_token_env_var`.

Export `CODEX_GITHUB_PERSONAL_ACCESS_TOKEN` from `~/.zshenv` so non-interactive Codex-launched
processes inherit it.

## Verification

```bash
codex mcp list
```

Expected: `github` appears with `npx`, `@modelcontextprotocol/server-github`, and
`GITHUB_PERSONAL_ACCESS_TOKEN=*****`. `Auth: Unsupported` is acceptable for stdio.

## Pattern

1. Read the actual `~/.codex/config.toml` block.
2. Classify MCP transport from fields: stdio uses `command`; HTTP uses `url`.
3. Apply auth fields only within that transport family.
4. Validate with `codex mcp list` after each change.

## Antipattern

Do not paste diagnostic text into config without schema-checking it for the active transport:

```toml
[mcp_servers.github]
bearer_token_env_var = "CODEX_GITHUB_PERSONAL_ACCESS_TOKEN"
```

That is the wrong shape for this stdio GitHub MCP setup.

## Postmortem Summary To Reuse

Codex failed because it classified the problem too late. It saw the warning mentioning
`bearer_token_env_var` and stayed in an auth frame. Claude won by running `codex mcp list`, reading
`invalid transport` as a schema failure, adding stdio `command`/`args`, and moving the PAT into
`[mcp_servers.github.env]`.

The durable rule is transport-specific, not absolute:

- Local npm GitHub MCP: stdio, use `command`/`args` plus `[mcp_servers.github.env]`.
- Remote GitHub MCP endpoint: HTTP, `url` plus `bearer_token_env_var` is valid.
- Always verify with `codex mcp get github` or `codex mcp list`.

## Related

- [Session log entry](../LESSONS.md)
- [Agent behavioral rules](../../SKILL.md)
