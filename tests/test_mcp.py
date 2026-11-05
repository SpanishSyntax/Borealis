"""Unit tests for Borealis Model Context Protocol (MCP) server."""

from __future__ import annotations

import json
from borealis.mcp import StdioMCPServer, TOOL_DEFINITIONS, execute_tool


def test_mcp_initialize() -> None:
    server = StdioMCPServer()
    req = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "test-agent", "version": "1.0"},
        },
    }
    resp = server.handle_request(req)
    assert resp is not None
    assert resp["id"] == 1
    assert resp["result"]["serverInfo"]["name"] == "borealis"
    assert resp["result"]["protocolVersion"] == "2024-11-05"


def test_mcp_tools_list() -> None:
    server = StdioMCPServer()
    req = {"jsonrpc": "2.0", "id": 2, "method": "tools/list"}
    resp = server.handle_request(req)
    assert resp is not None
    tools = resp["result"]["tools"]
    tool_names = [t["name"] for t in tools]
    assert "borealis_status" in tool_names


def test_mcp_ping() -> None:
    server = StdioMCPServer()
    req = {"jsonrpc": "2.0", "id": 3, "method": "ping"}
    resp = server.handle_request(req)
    assert resp == {"jsonrpc": "2.0", "id": 3, "result": {}}


def test_mcp_unknown_method() -> None:
    server = StdioMCPServer()
    req = {"jsonrpc": "2.0", "id": 4, "method": "unknown/method"}
    resp = server.handle_request(req)
    assert resp is not None
    assert "error" in resp
    assert resp["error"]["code"] == -32601


def test_execute_borealis_status() -> None:
    res = execute_tool("borealis_status", {"force": False})
    assert res["status"] == "ok"
    assert "timestamp" in res
    assert "mood" in res
    assert "tags" in res
    assert "context" in res
    assert "indexed_wallpapers" in res
    assert isinstance(res["context"], dict)


def test_execute_unknown_tool() -> None:
    res = execute_tool("nonexistent_tool", {})
    assert res["status"] == "error"
    assert "Unknown tool" in res["error"]


def test_mcp_tools_call_handler() -> None:
    server = StdioMCPServer()
    req = {
        "jsonrpc": "2.0",
        "id": 10,
        "method": "tools/call",
        "params": {
            "name": "borealis_status",
            "arguments": {"force": False},
        },
    }
    resp = server.handle_request(req)
    assert resp is not None
    assert resp["id"] == 10
    content = resp["result"]["content"]
    assert len(content) == 1
    assert content[0]["type"] == "text"
    parsed = json.loads(content[0]["text"])
    assert parsed["status"] == "ok"
    assert "mood" in parsed
    assert "context" in parsed
