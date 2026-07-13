"""Core drift-detection logic: compare a baseline tool set to a current one."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .models import ToolDefinition
from .rules import severity_for_new_tags
from .semantic import SimilarityBackend, default_backend

# Below this similarity score, two descriptions are considered to have
# drifted in *meaning*, not just wording. Chosen empirically: eval/run_eval.py
# sweeps thresholds 0.05-0.90 against the labeled fixture set and found
# perfect accuracy (4/4) for any threshold in [0.15, 0.50]. 0.35 is picked
# from the middle of that safe band, rather than an edge value, to leave
# margin on both sides -- the benign-rewrite fixture alone measured 0.536
# similarity, uncomfortably close to the top of that band, so hugging 0.50
# would risk false positives on ordinary doc-string cleanups in practice.
SEMANTIC_DRIFT_THRESHOLD = 0.35


@dataclass
class DriftFinding:
    tool_name: str
    kind: str  # new_tool | removed_tool | schema_changed | text_drift | capability_escalation
    severity: str  # info | low | high | critical
    details: str
    similarity: Optional[float] = None

    def to_dict(self) -> Dict:
        return {
            "tool": self.tool_name,
            "kind": self.kind,
            "severity": self.severity,
            "details": self.details,
            "similarity": self.similarity,
        }


@dataclass
class DriftReport:
    findings: List[DriftFinding] = field(default_factory=list)

    @property
    def has_critical(self) -> bool:
        return any(f.severity == "critical" for f in self.findings)

    @property
    def has_blocking(self) -> bool:
        return any(f.severity in ("high", "critical") for f in self.findings)

    def to_dict(self) -> Dict:
        return {
            "finding_count": len(self.findings),
            "has_critical": self.has_critical,
            "has_blocking": self.has_blocking,
            "findings": [f.to_dict() for f in self.findings],
        }


def compare(
    baseline: Dict[str, ToolDefinition],
    current: Dict[str, ToolDefinition],
    backend: Optional[SimilarityBackend] = None,
    semantic_threshold: float = SEMANTIC_DRIFT_THRESHOLD,
) -> DriftReport:
    backend = backend or default_backend()
    report = DriftReport()

    baseline_names = set(baseline.keys())
    current_names = set(current.keys())

    for name in current_names - baseline_names:
        report.findings.append(
            DriftFinding(
                tool_name=name,
                kind="new_tool",
                severity="low",
                details="Tool was not present in the trusted baseline. Review before trusting.",
            )
        )

    for name in baseline_names - current_names:
        report.findings.append(
            DriftFinding(
                tool_name=name,
                kind="removed_tool",
                severity="info",
                details="Tool present in baseline is no longer offered by the server.",
            )
        )

    for name in baseline_names & current_names:
        old, new = baseline[name], current[name]

        if old.content_hash() == new.content_hash():
            continue

        sim = backend.similarity(old.description, new.description)
        severity = severity_for_new_tags(old.permissions, new.permissions)

        gained = sorted(set(new.permissions) - set(old.permissions))
        lost = sorted(set(old.permissions) - set(new.permissions))

        if gained:
            report.findings.append(
                DriftFinding(
                    tool_name=name,
                    kind="capability_escalation",
                    severity=severity,
                    details=(
                        f"Tool gained capability signal(s) {gained} not present in the "
                        f"trusted baseline (lost: {lost or 'none'}). description_similarity="
                        f"{sim:.2f}."
                    ),
                    similarity=sim,
                )
            )
        elif sim < semantic_threshold:
            report.findings.append(
                DriftFinding(
                    tool_name=name,
                    kind="text_drift",
                    severity="high",
                    details=(
                        f"Description changed and fell below the semantic-similarity "
                        f"threshold ({sim:.2f} < {semantic_threshold}). No new capability "
                        f"keywords were detected, but the wording changed enough that a "
                        f"human should re-review intent (classic 'rug pull' pattern: same "
                        f"surface capabilities, different real behavior)."
                    ),
                    similarity=sim,
                )
            )
        elif old.input_schema != new.input_schema:
            report.findings.append(
                DriftFinding(
                    tool_name=name,
                    kind="schema_changed",
                    severity="low",
                    details="Input schema changed but description/capabilities look stable.",
                    similarity=sim,
                )
            )
        else:
            report.findings.append(
                DriftFinding(
                    tool_name=name,
                    kind="text_drift",
                    severity="info",
                    details=f"Minor wording change, similarity={sim:.2f}, no capability change.",
                    similarity=sim,
                )
            )

    return report
