"""Persisting and loading trusted snapshots of a tool set."""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Dict, List

from .models import ToolDefinition


def save_snapshot(tools: List[ToolDefinition], path: str) -> None:
    payload = {
        "created_at": time.time(),
        "tool_count": len(tools),
        "tools": {t.name: t.to_dict() for t in tools},
    }
    Path(path).write_text(json.dumps(payload, indent=2, sort_keys=True))


def load_snapshot(path: str) -> Dict[str, ToolDefinition]:
    payload = json.loads(Path(path).read_text())
    tools_raw = payload.get("tools", {})
    return {name: ToolDefinition.from_dict(d) for name, d in tools_raw.items()}
