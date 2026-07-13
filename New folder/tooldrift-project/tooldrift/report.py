"""Human-readable rendering of a DriftReport (used by the CLI)."""
from __future__ import annotations

from .diff import DriftReport

_SEVERITY_ICON = {
    "critical": "[CRITICAL]",
    "high": "[HIGH]",
    "low": "[LOW]",
    "info": "[INFO]",
}


def render_text(report: DriftReport) -> str:
    if not report.findings:
        return "tooldrift: no drift detected. All tools match the trusted baseline.\n"

    lines = [f"tooldrift: {len(report.findings)} finding(s)\n"]
    order = {"critical": 0, "high": 1, "low": 2, "info": 3}
    for f in sorted(report.findings, key=lambda x: order.get(x.severity, 9)):
        icon = _SEVERITY_ICON.get(f.severity, f.severity.upper())
        lines.append(f"{icon} {f.tool_name} ({f.kind})")
        lines.append(f"    {f.details}")
    if report.has_critical:
        lines.append(
            "\nRESULT: CRITICAL drift detected -- likely capability escalation "
            "(MCP rug pull pattern). Failing build."
        )
    elif report.has_blocking:
        lines.append("\nRESULT: High-severity drift detected. Review required.")
    else:
        lines.append("\nRESULT: Only informational/low-severity drift. Not blocking.")
    return "\n".join(lines) + "\n"
