"""Tests for Model Context Protocol (MCP) server endpoints."""
from __future__ import annotations

import json
from pathlib import Path
from tools.mcp_server import process_json_rpc


def test_mcp_tools_list() -> None:
    req = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/list",
        "params": {},
    }
    resp = process_json_rpc(req)
    assert resp is not None
    assert resp["id"] == 1
    tools = resp["result"]["tools"]
    tool_names = [t["name"] for t in tools]
    assert "list_resources" in tool_names
    assert "explain_graph" in tool_names
    assert "generate_diagram" in tool_names


def test_mcp_list_resources() -> None:
    req = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/call",
        "params": {
            "name": "list_resources",
            "arguments": {"path": "examples/terraform/aws-basic/main.tf"},
        },
    }
    resp = process_json_rpc(req)
    assert resp is not None
    assert resp["id"] == 2
    res = resp["result"]
    assert "resource_count" in res
    assert res["resource_count"] > 0
    assert any("aws_instance" in r for r in res["resources"])


def test_mcp_explain_graph() -> None:
    req = {
        "jsonrpc": "2.0",
        "id": 3,
        "method": "tools/call",
        "params": {
            "name": "explain_graph",
            "arguments": {"path": "examples/terraform/aws-basic/main.tf"},
        },
    }
    resp = process_json_rpc(req)
    assert resp is not None
    assert resp["id"] == 3
    res = resp["result"]
    assert "summary" in res
    assert "by_provider" in res
    assert "aws" in res["by_provider"]
