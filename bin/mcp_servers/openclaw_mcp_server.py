"""
OpenClaw MCP Server — stdio JSON-RPC server with OpenClaw gateway integration.
Four tools: openclaw_chat, openclaw_list_agents, openclaw_orchestrate, openclaw_health.

Adapted from bin/mcp_servers/lmstudio_mcp_server.py.
All model calls now route through the OpenClaw gateway at 127.0.0.1:18789
instead of directly hitting LM Studio endpoints.

Orchestration: dispatch roles sequentially or in parallel by agent_id.
OpenClaw resolves each agent_id to the correct provider and hardware.
"""
import asyncio
import json
import sys
from datetime import datetime

from bin.mcp_servers.openclaw_bridge import chat, list_models, health, OPENCLAW_GATEWAY

ORCHESTRATE_ROLES = ["coder", "checker", "refiner", "executor", "verifier"]


class MCP_JSONRPCServer:
    """Minimal MCP stdio JSON-RPC server."""

    def __init__(self):
        self.request_id = None

    async def handle_initialize(self, params):
        return {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {"listChanged": False}},
            "serverInfo": {"name": "ultrathink-openclaw", "version": "1.0.0"},
        }

    async def handle_tools_list(self, params):
        return {
            "tools": [
                {
                    "name": "openclaw_chat",
                    "description": "Send a chat request through the OpenClaw gateway to a named agent",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "input": {"type": "string", "description": "Chat prompt / task"},
                            "agent_id": {
                                "type": "string",
                                "description": "OpenClaw agent ID (default: orchestrator)",
                            },
                            "context_length": {
                                "type": "integer",
                                "description": "max_tokens (default: 4096)",
                            },
                        },
                        "required": ["input"],
                    },
                },
                {
                    "name": "openclaw_list_agents",
                    "description": "List agents registered in ~/.openclaw/openclaw.json via gateway /v1/models",
                    "inputSchema": {"type": "object", "properties": {}, "required": []},
                },
                {
                    "name": "openclaw_orchestrate",
                    "description": (
                        "Orchestrate a task across multiple agent roles via OpenClaw. "
                        "Dispatches roles sequentially (single agent) or in parallel (multiple agents)."
                    ),
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "task": {"type": "string", "description": "Work description"},
                            "roles": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Agent IDs / role sequence (default: coder→checker→refiner→executor→verifier)",
                            },
                            "parallel": {
                                "type": "boolean",
                                "description": "Dispatch all roles in parallel (default: false = sequential)",
                            },
                            "synthesize": {
                                "type": "boolean",
                                "description": "Orchestrator validates final output (default: true)",
                            },
                            "max_cycles": {
                                "type": "integer",
                                "description": "Orchestration cycles (default: 1)",
                            },
                        },
                        "required": ["task"],
                    },
                },
                {
                    "name": "openclaw_health",
                    "description": "Check if the OpenClaw gateway is reachable at 127.0.0.1:18789",
                    "inputSchema": {"type": "object", "properties": {}, "required": []},
                },
            ]
        }

    async def handle_tools_call(self, params):
        name = params.get("name")
        args = params.get("arguments", {})

        if name == "openclaw_chat":
            return await self._tool_chat(args)
        elif name == "openclaw_list_agents":
            return await self._tool_list_agents(args)
        elif name == "openclaw_orchestrate":
            return await self._tool_orchestrate(args)
        elif name == "openclaw_health":
            return await self._tool_health(args)
        else:
            raise ValueError(f"Unknown tool: {name}")

    async def _tool_chat(self, args):
        input_text = args.get("input", "")
        agent_id = args.get("agent_id", "orchestrator")
        context_length = args.get("context_length", 4096)
        if not input_text:
            return {"error": "input is required"}
        try:
            return await chat(agent_id, input_text, context_length)
        except Exception as e:
            return {"error": str(e)}

    async def _tool_list_agents(self, args):
        try:
            agents = await list_models()
            return {"agents": agents, "gateway": OPENCLAW_GATEWAY}
        except Exception as e:
            return {"error": str(e)}

    async def _tool_orchestrate(self, args):
        task = args.get("task", "")
        roles = args.get("roles", ORCHESTRATE_ROLES)
        parallel = args.get("parallel", False)
        synthesize = args.get("synthesize", True)
        max_cycles = args.get("max_cycles", 1)

        if not task:
            return {"error": "task is required"}

        start_time = datetime.now()
        cycle_results = []

        for cycle in range(max_cycles):
            if parallel:
                async def _dispatch(role):
                    try:
                        r = await chat(role, task, 4096)
                        return {"role": role, "output": r.get("content", ""), "tokens": r.get("tokens", 0)}
                    except Exception as e:
                        return {"role": role, "error": str(e)}

                role_results = list(await asyncio.gather(*[_dispatch(r) for r in roles]))
            else:
                role_results = []
                context = task
                for role in roles:
                    prompt = f"[{role.upper()}] {context}"
                    try:
                        r = await chat(role, prompt, 4096)
                        output = r.get("content", "")
                        role_results.append({"role": role, "output": output, "tokens": r.get("tokens", 0)})
                        context = output  # chain output as next context
                    except Exception as e:
                        role_results.append({"role": role, "error": str(e)})

            synthesis = None
            if synthesize:
                best = next((r.get("output", "") for r in role_results if "error" not in r), "")
                if best:
                    try:
                        val = await chat("orchestrator", f"Validate and synthesise:\n{best}", 4096)
                        synthesis = {"validated": True, "output": val.get("content", ""), "tokens": val.get("tokens", 0)}
                    except Exception as e:
                        synthesis = {"validated": False, "error": str(e)}

            cycle_results.append({"cycle": cycle + 1, "role_results": role_results, "synthesis": synthesis})

        elapsed_ms = int((datetime.now() - start_time).total_seconds() * 1000)
        return {
            "cycles": cycle_results,
            "total_cycles": len(cycle_results),
            "elapsed_ms": elapsed_ms,
            "final_output": (cycle_results[-1].get("synthesis") or {}).get("output", ""),
        }

    async def _tool_health(self, args):
        ok = await health()
        agents = []
        if ok:
            try:
                agents = await list_models()
            except Exception:
                pass
        return {"gateway_ok": ok, "gateway_url": OPENCLAW_GATEWAY, "agents": agents}

    async def process_message(self, message):
        try:
            self.request_id = message.get("id")
            method = message.get("method")
            params = message.get("params", {})

            if method == "initialize":
                result = await self.handle_initialize(params)
            elif method == "tools/list":
                result = await self.handle_tools_list(params)
            elif method == "tools/call":
                result = await self.handle_tools_call(params)
            else:
                result = None

            return {"jsonrpc": "2.0", "id": self.request_id, "result": result}
        except Exception as e:
            return {
                "jsonrpc": "2.0",
                "id": self.request_id,
                "error": {"code": -32603, "message": str(e)},
            }

    async def run(self):
        while True:
            try:
                line = sys.stdin.readline()
                if not line:
                    break
                message = json.loads(line)
                response = await self.process_message(message)
                sys.stdout.write(json.dumps(response) + "\n")
                sys.stdout.flush()
            except json.JSONDecodeError:
                pass
            except Exception as e:
                sys.stderr.write(f"Error: {e}\n")


async def main():
    server = MCP_JSONRPCServer()
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())
