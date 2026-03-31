"""
LM Studio MCP Server — stdio JSON-RPC server with orchestration support.
Four tools: lmstudio_chat, lmstudio_list_models, lmstudio_orchestrate, lmstudio_health.

Orchestration cycle: Mac dispatcher → Win agents (sequential or 1-4 parallel) →
Mac validator → optional cloud verify → Mac presenter.
"""
import asyncio
import json
import sys
import os
from typing import Optional
from datetime import datetime

from multi_agent.mcp_servers.lmstudio_bridge import (
    chat,
    list_models,
    health,
    LMS_MAC_ENDPOINT,
    LMS_WIN_ENDPOINTS,
    LMS_API_TOKEN,
    LMS_WIN_MAX_PARALLEL,
)


class MCP_JSONRPCServer:
    """Minimal MCP stdio JSON-RPC server."""

    def __init__(self):
        self.request_id = None

    async def handle_initialize(self, params):
        """Initialize handshake."""
        return {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {
                    "listChanged": False,
                }
            },
            "serverInfo": {
                "name": "ultrathink-lmstudio",
                "version": "1.0.0-rc",
            },
        }

    async def handle_tools_list(self, params):
        """List available tools."""
        return {
            "tools": [
                {
                    "name": "lmstudio_chat",
                    "description": "Send a chat request to LM Studio endpoint (Mac or Win)",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "input": {
                                "type": "string",
                                "description": "Chat prompt/task",
                            },
                            "model": {
                                "type": "string",
                                "description": "Model ID (optional, uses first available if omitted)",
                            },
                            "endpoint": {
                                "type": "string",
                                "enum": ["mac", "win", "auto"],
                                "description": "Target endpoint (default: auto)",
                            },
                            "context_length": {
                                "type": "integer",
                                "description": "Max tokens (default: 4096)",
                            },
                        },
                        "required": ["input"],
                    },
                },
                {
                    "name": "lmstudio_list_models",
                    "description": "List models on LM Studio endpoints (Mac, Win, or both)",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "endpoint": {
                                "type": "string",
                                "enum": ["mac", "win", "both"],
                                "description": "Which endpoint(s) to query (default: both)",
                            },
                        },
                        "required": [],
                    },
                },
                {
                    "name": "lmstudio_orchestrate",
                    "description": "Orchestrate task across Mac (dispatcher/validator) and Win agent(s). Sequential or parallel dispatch.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "task": {
                                "type": "string",
                                "description": "Work description for Win agents",
                            },
                            "roles": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Role sequence (default: [coder, checker, refiner, executor, verifier])",
                            },
                            "win_endpoints": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Override Win endpoints (max 4, default: LMS_WIN_ENDPOINTS)",
                            },
                            "synthesize": {
                                "type": "boolean",
                                "description": "Mac validates output (default: true)",
                            },
                            "cloud_verify": {
                                "type": "boolean",
                                "description": "Use cloud verification step if online (default: false)",
                            },
                            "max_cycles": {
                                "type": "integer",
                                "description": "Number of orchestration cycles (default: 1)",
                            },
                        },
                        "required": ["task"],
                    },
                },
                {
                    "name": "lmstudio_health",
                    "description": "Check health of Mac and Win LM Studio endpoints",
                    "inputSchema": {
                        "type": "object",
                        "properties": {},
                        "required": [],
                    },
                },
            ]
        }

    async def handle_tools_call(self, params):
        """Handle tool calls."""
        name = params.get("name")
        args = params.get("arguments", {})

        if name == "lmstudio_chat":
            return await self._tool_chat(args)
        elif name == "lmstudio_list_models":
            return await self._tool_list_models(args)
        elif name == "lmstudio_orchestrate":
            return await self._tool_orchestrate(args)
        elif name == "lmstudio_health":
            return await self._tool_health(args)
        else:
            raise ValueError(f"Unknown tool: {name}")

    async def _tool_chat(self, args):
        """lmstudio_chat tool implementation."""
        input_text = args.get("input", "")
        model = args.get("model", "")
        endpoint_choice = args.get("endpoint", "auto").lower()
        context_length = args.get("context_length", 4096)

        if not input_text:
            return {"error": "input is required"}

        # Determine endpoint
        if endpoint_choice == "mac":
            endpoint = LMS_MAC_ENDPOINT
        elif endpoint_choice == "win":
            endpoint = LMS_WIN_ENDPOINTS[0] if LMS_WIN_ENDPOINTS else None
        else:  # auto
            endpoint = LMS_MAC_ENDPOINT

        if not endpoint:
            return {"error": "No endpoint available"}

        # Fetch models if not specified
        if not model:
            try:
                models = await list_models(endpoint, LMS_API_TOKEN)
                model = models[0] if models else ""
            except Exception as e:
                return {"error": f"Failed to fetch models: {str(e)}"}

        # Chat
        try:
            result = await chat(
                endpoint,
                model,
                input_text,
                context_length,
                token=LMS_API_TOKEN,
            )
            return result
        except Exception as e:
            return {"error": f"Chat failed: {str(e)}"}

    async def _tool_list_models(self, args):
        """lmstudio_list_models tool implementation."""
        endpoint_choice = args.get("endpoint", "both").lower()

        result = {}

        if endpoint_choice in ["mac", "both"]:
            try:
                mac_models = await list_models(LMS_MAC_ENDPOINT, LMS_API_TOKEN)
                result["mac"] = mac_models
            except Exception as e:
                result["mac_error"] = str(e)

        if endpoint_choice in ["win", "both"]:
            try:
                win_models = await list_models(
                    LMS_WIN_ENDPOINTS[0], LMS_API_TOKEN
                )
                result["win"] = win_models
            except Exception as e:
                result["win_error"] = str(e)

        return result

    async def _tool_orchestrate(self, args):
        """lmstudio_orchestrate tool implementation — main MVP tool."""
        task = args.get("task", "")
        roles = args.get("roles", ["coder", "checker", "refiner", "executor", "verifier"])
        win_endpoints = args.get("win_endpoints")
        if win_endpoints is None:
            win_endpoints = LMS_WIN_ENDPOINTS
        # Cap at LMS_WIN_MAX_PARALLEL
        win_endpoints = win_endpoints[: LMS_WIN_MAX_PARALLEL]

        synthesize = args.get("synthesize", True)
        cloud_verify = args.get("cloud_verify", False)
        max_cycles = args.get("max_cycles", 1)

        if not task:
            return {"error": "task is required"}

        start_time = datetime.now()
        cycle_results = []

        for cycle in range(max_cycles):
            # === CYCLE: Dispatch to Win agents ===
            win_results = []

            if len(win_endpoints) == 1:
                # Sequential: roles → single endpoint
                for role in roles:
                    role_prompt = f"[{role.upper()}] {task}"
                    try:
                        result = await chat(
                            win_endpoints[0],
                            "",  # auto-select model
                            role_prompt,
                            16384,
                            token=LMS_API_TOKEN,
                        )
                        win_results.append(
                            {
                                "role": role,
                                "endpoint": win_endpoints[0],
                                "output": result.get("content", ""),
                                "tokens": result.get("tokens", 0),
                            }
                        )
                    except Exception as e:
                        win_results.append(
                            {
                                "role": role,
                                "endpoint": win_endpoints[0],
                                "error": str(e),
                            }
                        )
            else:
                # Parallel: same task to each endpoint
                async def dispatch_to_endpoint(ep):
                    try:
                        result = await chat(
                            ep,
                            "",  # auto-select model
                            task,
                            16384,
                            token=LMS_API_TOKEN,
                        )
                        return {
                            "endpoint": ep,
                            "output": result.get("content", ""),
                            "tokens": result.get("tokens", 0),
                        }
                    except Exception as e:
                        return {"endpoint": ep, "error": str(e)}

                win_results = await asyncio.gather(
                    *[dispatch_to_endpoint(ep) for ep in win_endpoints]
                )

            # === Mac Validation ===
            mac_validation = None
            if synthesize:
                # Mac validates best Win output
                best_result = None
                for res in win_results:
                    if "error" not in res:
                        best_result = res.get("output", "")
                        break

                if best_result:
                    val_prompt = f"Validate and refine:\n{best_result}"
                    try:
                        validation = await chat(
                            LMS_MAC_ENDPOINT,
                            "",
                            val_prompt,
                            4096,
                            token=LMS_API_TOKEN,
                        )
                        mac_validation = {
                            "validated": True,
                            "output": validation.get("content", ""),
                            "tokens": validation.get("tokens", 0),
                        }
                    except Exception as e:
                        mac_validation = {"validated": False, "error": str(e)}

            cycle_results.append(
                {
                    "cycle": cycle + 1,
                    "win_results": win_results,
                    "mac_validation": mac_validation,
                }
            )

        elapsed_ms = int((datetime.now() - start_time).total_seconds() * 1000)

        return {
            "cycles": cycle_results,
            "total_cycles": len(cycle_results),
            "elapsed_ms": elapsed_ms,
            "final_output": (
                cycle_results[-1].get("mac_validation", {}).get("output", "")
                if cycle_results
                else ""
            ),
            "cloud_verify": cloud_verify,
        }

    async def _tool_health(self, args):
        """lmstudio_health tool implementation."""
        mac_ok = await health(LMS_MAC_ENDPOINT, LMS_API_TOKEN)
        mac_models = []
        if mac_ok:
            try:
                mac_models = await list_models(LMS_MAC_ENDPOINT, LMS_API_TOKEN)
            except:
                pass

        win_endpoints_status = []
        for ep in LMS_WIN_ENDPOINTS:
            ep_ok = await health(ep, LMS_API_TOKEN)
            ep_models = []
            if ep_ok:
                try:
                    ep_models = await list_models(ep, LMS_API_TOKEN)
                except:
                    pass
            win_endpoints_status.append(
                {"url": ep, "ok": ep_ok, "models": ep_models}
            )

        return {
            "mac_ok": mac_ok,
            "mac_models": mac_models,
            "mac_endpoint": LMS_MAC_ENDPOINT,
            "win_endpoints": win_endpoints_status,
            "max_parallel": LMS_WIN_MAX_PARALLEL,
        }

    async def process_message(self, message):
        """Process one JSON-RPC message."""
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
                error = f"Unknown method: {method}"

            if error := message.get("_error"):
                return {
                    "jsonrpc": "2.0",
                    "id": self.request_id,
                    "error": {"code": -32601, "message": error},
                }

            return {
                "jsonrpc": "2.0",
                "id": self.request_id,
                "result": result,
            }
        except Exception as e:
            return {
                "jsonrpc": "2.0",
                "id": self.request_id,
                "error": {"code": -32603, "message": str(e)},
            }

    async def run(self):
        """Main event loop — read JSON-RPC messages from stdin."""
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
