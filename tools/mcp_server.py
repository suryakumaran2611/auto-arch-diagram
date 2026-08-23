"""Model Context Protocol (MCP) server for auto-arch-diagram.

Provides stdio JSON-RPC 2.0 endpoints for AI agents and IDE extensions:
- generate_diagram: Generate architecture diagrams in multiple formats (PNG, SVG, Mermaid, HTML, draw.io).
- list_resources: Parse IaC files and return structured list of resources and providers.
- explain_graph: Analyze topology and return architectural relationships and containment summary.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT / "tools") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "tools"))

from generate_arch_diagram import (
    Limits,
    RenderConfig,
    _filter_architectural_edges,
    _static_terraform_mermaid,
    _terraform_resources_from_files,
    _tf_category,
)


def handle_list_resources(args: dict[str, Any]) -> dict[str, Any]:
    """List resources extracted from Terraform or IaC files."""
    iac_path = Path(args.get("path", "."))
    if not iac_path.is_absolute():
        iac_path = REPO_ROOT / iac_path

    tf_files = []
    if iac_path.is_file():
        tf_files.append(iac_path)
    elif iac_path.is_dir():
        tf_files.extend(iac_path.glob("*.tf"))

    all_resources, _, _ = _terraform_resources_from_files(tf_files, Limits(), REPO_ROOT)
    res_list = sorted(all_resources.keys())
    return {
        "file_count": len(tf_files),
        "resource_count": len(res_list),
        "resources": res_list,
    }


def handle_explain_graph(args: dict[str, Any]) -> dict[str, Any]:
    """Explain topology and key infrastructure components."""
    res = handle_list_resources(args)
    resources = res.get("resources", [])

    by_provider: dict[str, list[str]] = {}
    by_category: dict[str, list[str]] = {}
    for r in resources:
        r_type = r.split(".")[0] if "." in r else r
        provider = "aws" if r_type.startswith("aws_") else ("azure" if r_type.startswith("azurerm_") else "gcp")
        cat = _tf_category(r_type)
        by_provider.setdefault(provider, []).append(r)
        by_category.setdefault(cat, []).append(r)

    return {
        "summary": f"Architecture contains {len(resources)} resources across {len(by_provider)} cloud providers.",
        "by_provider": {k: len(v) for k, v in by_provider.items()},
        "by_category": {k: len(v) for k, v in by_category.items()},
        "resources": resources,
    }


def handle_generate_diagram(args: dict[str, Any]) -> dict[str, Any]:
    """Generate diagrams from IaC files."""
    import subprocess
    target_path = args.get("path", "examples/terraform/aws-basic/main.tf")
    out_dir = Path(args.get("out_dir", "artifacts"))
    out_dir.mkdir(parents=True, exist_ok=True)

    cmd = [
        sys.executable,
        str(REPO_ROOT / "tools" / "generate_arch_diagram.py"),
        "--changed-files",
        target_path,
        "--out-png",
        str(out_dir / "diagram.png"),
        "--out-svg",
        str(out_dir / "diagram.svg"),
        "--out-mmd",
        str(out_dir / "diagram.mmd"),
    ]

    res = subprocess.run(cmd, cwd=str(REPO_ROOT), capture_output=True, text=True)
    return {
        "success": res.returncode == 0,
        "stdout": res.stdout,
        "stderr": res.stderr,
        "generated_files": [
            str(out_dir / "diagram.png"),
            str(out_dir / "diagram.svg"),
            str(out_dir / "diagram.mmd"),
        ],
    }


TOOLS = {
    "list_resources": handle_list_resources,
    "explain_graph": handle_explain_graph,
    "generate_diagram": handle_generate_diagram,
}


def process_json_rpc(message: dict[str, Any]) -> Optional[dict[str, Any]]:
    """Process single JSON-RPC 2.0 request."""
    req_id = message.get("id")
    method = message.get("method")
    params = message.get("params", {})

    if method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "tools": [
                    {
                        "name": "list_resources",
                        "description": "Parse IaC files and return structured list of resources.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {"path": {"type": "string"}},
                        },
                    },
                    {
                        "name": "explain_graph",
                        "description": "Explain infrastructure architecture topology and categorizations.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {"path": {"type": "string"}},
                        },
                    },
                    {
                        "name": "generate_diagram",
                        "description": "Generate architecture diagrams in multiple formats.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "path": {"type": "string"},
                                "out_dir": {"type": "string"},
                            },
                        },
                    },
                ]
            },
        }

    if method == "tools/call":
        tool_name = params.get("name")
        tool_args = params.get("arguments", {})
        if tool_name in TOOLS:
            try:
                result = TOOLS[tool_name](tool_args)
                return {"jsonrpc": "2.0", "id": req_id, "result": result}
            except Exception as e:
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {"code": -32603, "message": str(e)},
                }
        else:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32601, "message": f"Method {tool_name} not found"},
            }

    return None


def run_stdio_server() -> None:
    """Run JSON-RPC MCP server on stdin / stdout."""
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
            resp = process_json_rpc(req)
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


if __name__ == "__main__":
    run_stdio_server()
