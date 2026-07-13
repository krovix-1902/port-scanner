"""
Extractors turn a "source" (a JSON export, or a live MCP server) into a
list of ToolDefinition objects.

Supported sources today:
  - static JSON file containing a `tools/list`-shaped response
    (either `{"tools": [...]}` or a bare list `[...]`)
  - a live MCP server over stdio, IF the `mcp` python SDK is installed
    (optional dependency -- kept optional so the core drift-detection
    logic has zero hard dependency on a live agent runtime, which makes
    it trivially unit-testable and easy to run in CI without secrets).
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from .models import ToolDefinition
from .rules import derive_capability_tags, extract_declared_annotations


def load_tools_from_json(path: str) -> List[ToolDefinition]:
    data = json.loads(Path(path).read_text())
    if isinstance(data, dict) and "tools" in data:
        raw_tools = data["tools"]
        server_name = data.get("server", Path(path).stem)
    elif isinstance(data, list):
        raw_tools = data
        server_name = Path(path).stem
    else:
        raise ValueError(f"Unrecognized tool export format in {path}")

    return [_from_raw(t, server_name) for t in raw_tools]


def _from_raw(raw: Dict[str, Any], server_name: str) -> ToolDefinition:
    name = raw.get("name", "<unnamed>")
    description = raw.get("description", "")
    schema = raw.get("inputSchema") or raw.get("input_schema") or {}

    declared = extract_declared_annotations(raw)
    observed_tags = derive_capability_tags(description, schema)

    # capability list = union of what the server *claims* (declared hints
    # that indicate risk) and what tooldrift *observes* from the text --
    # deliberately conservative: a rug pull that lies in its annotations
    # should still get caught by the observed-tag layer.
    declared_risk_tags = []
    if declared.get("destructiveHint"):
        declared_risk_tags.append("destructive")
    if declared.get("openWorldHint"):
        declared_risk_tags.append("network")

    permissions = sorted(set(observed_tags) | set(declared_risk_tags))

    return ToolDefinition(
        name=name,
        description=description,
        input_schema=schema,
        permissions=permissions,
        server=server_name,
        raw=raw,
    )


async def load_tools_from_live_server(command: List[str]) -> List[ToolDefinition]:
    """Best-effort live extraction via the official `mcp` SDK stdio client.

    Kept separate from the JSON path so the rest of tooldrift (and all
    unit tests) never require a live subprocess or network access.
    """
    try:
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client
    except ImportError as exc:  # pragma: no cover - optional dependency
        raise RuntimeError(
            "Live MCP extraction requires the optional 'mcp' package: "
            "pip install mcp"
        ) from exc

    params = StdioServerParameters(command=command[0], args=command[1:])
    tools: List[ToolDefinition] = []
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.list_tools()
            for tool in result.tools:
                raw = tool.model_dump() if hasattr(tool, "model_dump") else dict(tool)
                tools.append(_from_raw(raw, server_name=" ".join(command)))
    return tools
