#!/usr/bin/env python3
"""
agent_communication_server.py
==============================
MCP Server: ultrathink Agent-to-Agent Communication
Version: 0.9.9.1 | License: Apache 2.0

Provides direct inter-agent messaging tools for sub-agent delegation
within the ultrathink network.

Tools:
    - agent_send    : Send message to a named agent
    - agent_receive : Receive message from queue (with timeout)
    - agent_list    : List active agents and their current tasks
"""
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "shared"))
from ultrathink_core import AgentMessage, MessageType
from state_manager import StateManager
from message_bus import MessageBus

TOOL_SCHEMAS = [
    {
        "name": "agent_send",
        "description": "Send a message to a specific ultrathink agent.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "to_agent":   {"type": "string"},
                "from_agent": {"type": "string", "default": "caller"},
                "payload":    {"type": "object"},
                "trace_id":   {"type": "string"}
            },
            "required": ["to_agent", "payload"]
        }
    },
    {
        "name": "agent_receive",
        "description": "Receive a pending message for a specific agent (with timeout).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "agent_id": {"type": "string"},
                "timeout":  {"type": "number", "default": 30.0}
            },
            "required": ["agent_id"]
        }
    },
    {
        "name": "agent_list",
        "description": "List all registered agents and their current status.",
        "inputSchema": {"type": "object", "properties": {}}
    }
]

class AgentCommunicationServer:
    def __init__(self):
        self.state = StateManager()
        self.bus   = MessageBus()

    async def handle_request(self, request: dict) -> dict:
        method = request.get("method", "")
        params = request.get("params", {})
        req_id = request.get("id")
        try:
            if method == "initialize":
                result = {"protocolVersion": "2024-11-05",
                          "capabilities": {"tools": {}},
                          "serverInfo": {"name": "agent-communication-server", "version": "2.0.0"}}
            elif method == "tools/list":
                result = {"tools": TOOL_SCHEMAS}
            elif method == "tools/call":
                result = await self._dispatch(params["name"], params.get("arguments", {}))
            else:
                return {"jsonrpc": "2.0", "id": req_id,
                        "error": {"code": -32601, "message": f"Unknown method: {method}"}}
            return {"jsonrpc": "2.0", "id": req_id, "result": result}
        except Exception as e:
            return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32603, "message": str(e)}}

    async def _dispatch(self, name: str, args: dict) -> dict:
        if name == "agent_send":
            msg = AgentMessage(
                from_agent=args.get("from_agent", "caller"),
                to_agent=args["to_agent"],
                message_type=MessageType.DELEGATE_TASK,
                payload=args["payload"],
                trace_id=args.get("trace_id", ""),
            )
            success = await self.bus.publish(msg)
            return {"sent": success, "message_id": msg.message_id, "trace_id": msg.trace_id}

        elif name == "agent_receive":
            msg = await self.bus.subscribe(args["agent_id"], timeout=args.get("timeout", 30.0))
            return msg or {"message": None, "timeout": True}

        elif name == "agent_list":
            # STUB: return registry from config
            config_path = Path(__file__).parent.parent / "config" / "agent_registry.json"
            if config_path.exists():
                registry = json.loads(config_path.read_text())
                return {"agents": [{"id": a["id"], "type": a["type"]} for a in registry["agents"]]}
            return {"agents": []}

        raise ValueError(f"Unknown tool: {name}")

async def run_stdio_server():
    server = AgentCommunicationServer()
    while True:
        try:
            line = await asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline)
            if not line: break
            response = await server.handle_request(json.loads(line.strip()))
            print(json.dumps(response), flush=True)
        except (json.JSONDecodeError, EOFError):
            break

if __name__ == "__main__":
    asyncio.run(run_stdio_server())
