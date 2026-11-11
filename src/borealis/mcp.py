"""Model Context Protocol (MCP) stdio server for Borealis."""

from __future__ import annotations

import contextlib
import datetime
import json
import sys
from typing import Any

from borealis import __version__
from borealis.config import load_config
from borealis.engine import BorealisEngine

TOOL_DEFINITIONS: list[dict[str, Any]] = [
    {
        "name": "borealis_status",
        "description": "Queries live celestial, space-weather, and solar wallpaper telemetry from Borealis.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "force": {
                    "type": "boolean",
                    "description": "Force live telemetry query instead of cached sensors (default: true).",
                    "default": True,
                }
            },
        },
    }
]


def execute_tool(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    """Execute a Borealis MCP tool call and return JSON-serializable results."""
    try:
        if name == "borealis_status":
            force = bool(arguments.get("force", True))
            config = load_config(None)

            # Redirect stdout to stderr to avoid polluting the JSON-RPC stdio protocol
            with contextlib.redirect_stdout(sys.stderr):
                engine = BorealisEngine(config)
                mood, tags, path, rule, ctx = engine.evaluate_and_pick(
                    force_telemetry=force
                )
                now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                return {
                    "status": "ok",
                    "timestamp": now,
                    "mood": mood,
                    "tags": tags,
                    "target_wallpaper": str(path) if path else None,
                    "rule": rule.name if rule else None,
                    "context": ctx,
                    "indexed_wallpapers": len(engine.library.items),
                }
        else:
            return {"status": "error", "error": f"Unknown tool: {name}"}
    except Exception as e:
        return {"status": "error", "error": str(e)}


class StdioMCPServer:
    """JSON-RPC 2.0 stdio server implementing the Model Context Protocol."""

    def __init__(self) -> None:
        self.server_info = {"name": "borealis", "version": __version__}

    def handle_request(self, req: dict[str, Any]) -> dict[str, Any] | None:
        method = req.get("method")
        msg_id = req.get("id")

        if method == "initialize":
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "serverInfo": self.server_info,
                    "capabilities": {"tools": {}},
                },
            }

        elif method == "notifications/initialized":
            return None

        elif method == "ping":
            return {"jsonrpc": "2.0", "id": msg_id, "result": {}}

        elif method == "tools/list":
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {"tools": TOOL_DEFINITIONS},
            }

        elif method == "tools/call":
            params = req.get("params", {})
            name = params.get("name", "")
            args = params.get("arguments", {})
            res = execute_tool(name, args)
            is_error = res.get("status") == "error"

            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "content": [{"type": "text", "text": json.dumps(res, indent=2)}],
                    "isError": is_error,
                },
            }

        else:
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "error": {"code": -32601, "message": f"Method not found: {method}"},
            }

    def run(self) -> None:
        """Run JSON-RPC event loop reading lines from sys.stdin."""
        for line in sys.stdin:
            line_str = line.strip()
            if not line_str:
                continue
            try:
                req = json.loads(line_str)
                resp = self.handle_request(req)
                if resp is not None:
                    sys.stdout.write(json.dumps(resp) + "\n")
                    sys.stdout.flush()
            except Exception as e:
                err_resp = {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {"code": -32700, "message": f"Parse error: {e}"},
                }
                sys.stdout.write(json.dumps(err_resp) + "\n")
                sys.stdout.flush()
