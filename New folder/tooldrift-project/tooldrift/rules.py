"""
Heuristic capability tagging.

The real MCP spec lets servers declare tool *annotations*
(readOnlyHint, destructiveHint, idempotentHint, openWorldHint) but these
are optional and frequently omitted or -- in a rug-pull attack -- simply
lied about. So on top of any declared annotations, tooldrift derives its
own capability tags from the tool's description and schema, and flags a
mismatch between "declared" and "observed" behavior as high severity.
"""
from __future__ import annotations

import re
from typing import Dict, List

# keyword -> capability tag. Deliberately simple/transparent (not an LLM
# call) so results are reproducible and auditable in CI logs.
_KEYWORD_TAGS = {
    r"\b(http|https|url|request|fetch|webhook|endpoint)\b": "network",
    r"\b(socket|dns|proxy|ssrf)\b": "network",
    r"\b(exec|subprocess|shell|command|os\.system|eval\()\b": "code-execution",
    r"\b(write|delete|remove|overwrite|modify)\b.*\b(file|disk|path)\b": "filesystem-write",
    r"\b(read)\b.*\b(file|disk|path)\b": "filesystem-read",
    r"\b(token|api[_ ]?key|secret|credential|password|auth)\b": "credential-access",
    r"\b(env|environment variable)\b": "environment-access",
    r"\b(send|upload|exfiltrate|transmit|post)\b.*\b(data|file|result)\b": "data-egress",
}

DECLARED_ANNOTATION_KEYS = (
    "readOnlyHint",
    "destructiveHint",
    "idempotentHint",
    "openWorldHint",
)


def derive_capability_tags(description: str, schema: Dict) -> List[str]:
    """Scan free-text description (+ schema property names) for capability signals."""
    text = (description or "").lower()
    schema_text = " ".join(_walk_schema_strings(schema)).lower()
    haystack = f"{text} {schema_text}"

    tags = set()
    for pattern, tag in _KEYWORD_TAGS.items():
        if re.search(pattern, haystack):
            tags.add(tag)
    return sorted(tags)


def _walk_schema_strings(schema: Dict) -> List[str]:
    out: List[str] = []
    if not isinstance(schema, dict):
        return out
    for key, value in schema.items():
        out.append(str(key))
        if isinstance(value, str):
            out.append(value)
        elif isinstance(value, dict):
            out.extend(_walk_schema_strings(value))
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    out.extend(_walk_schema_strings(item))
                else:
                    out.append(str(item))
    return out


def extract_declared_annotations(raw_tool: Dict) -> Dict[str, bool]:
    annotations = raw_tool.get("annotations", {}) if isinstance(raw_tool, dict) else {}
    return {k: annotations.get(k) for k in DECLARED_ANNOTATION_KEYS if k in annotations}


def severity_for_new_tags(old_tags: List[str], new_tags: List[str]) -> str:
    """Escalation of capability is high severity; simple wording changes with
    no new tags are low severity."""
    gained = set(new_tags) - set(old_tags)
    high_risk_gain = gained & {
        "code-execution",
        "credential-access",
        "data-egress",
        "filesystem-write",
        "network",
    }
    if high_risk_gain:
        return "critical"
    if gained:
        return "high"
    return "info"
