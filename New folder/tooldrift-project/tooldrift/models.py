"""Core data model for an MCP tool definition."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class ToolDefinition:
    """A single MCP tool as exposed by a server (or exported to JSON)."""

    name: str
    description: str
    input_schema: Dict[str, Any] = field(default_factory=dict)
    permissions: List[str] = field(default_factory=list)
    server: str = "unknown"
    raw: Dict[str, Any] = field(default_factory=dict)

    def content_hash(self) -> str:
        """Stable hash over the fields that define this tool's *behavior contract*."""
        payload = json.dumps(
            {
                "name": self.name,
                "description": self.description,
                "input_schema": self.input_schema,
                "permissions": sorted(self.permissions),
            },
            sort_keys=True,
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_schema,
            "permissions": self.permissions,
            "server": self.server,
            "content_hash": self.content_hash(),
        }

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "ToolDefinition":
        return ToolDefinition(
            name=d["name"],
            description=d.get("description", ""),
            input_schema=d.get("input_schema", {}),
            permissions=d.get("permissions", []),
            server=d.get("server", "unknown"),
            raw=d,
        )
