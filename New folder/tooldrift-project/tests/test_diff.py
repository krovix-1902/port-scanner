"""
Unit tests for the core drift-detection logic, run against the labeled
fixture pairs in tests/fixtures/. These are the same fixtures used by
eval/run_eval.py to compute aggregate precision/recall -- kept here too
so a single `pytest` catches regressions without needing the eval script.
"""
import json
from pathlib import Path

import pytest

from tooldrift.diff import compare
from tooldrift.extractor import load_tools_from_json

FIXTURES = Path(__file__).parent / "fixtures"
LABELS = json.loads((FIXTURES / "labels.json").read_text())


def _load(name: str, version: str):
    tools = load_tools_from_json(str(FIXTURES / f"{name}_{version}.json"))
    return {t.name: t for t in tools}


@pytest.mark.parametrize("case_name", ["benign", "rugpull", "reword", "addremove"])
def test_fixture_matches_expected_label(case_name):
    baseline = _load(case_name, "v1")
    current = _load(case_name, "v2")
    label = LABELS[case_name]

    report = compare(baseline, current)
    kinds_found = {f.kind for f in report.findings}

    assert report.has_blocking == label["expect_blocking"], (
        f"{case_name}: expected has_blocking={label['expect_blocking']}, "
        f"got {report.has_blocking}. Findings: {report.to_dict()}"
    )

    for expected_kind in label["expect_kinds"]:
        assert expected_kind in kinds_found, (
            f"{case_name}: expected finding kind '{expected_kind}' not found. "
            f"Findings: {kinds_found}"
        )

    if "expect_severity" in label:
        severities_found = {f.severity for f in report.findings}
        assert label["expect_severity"] in severities_found


def test_identical_snapshots_produce_no_findings():
    baseline = _load("benign", "v1")
    current = _load("benign", "v1")
    report = compare(baseline, current)
    assert report.findings == []
    assert not report.has_blocking


def test_rugpull_is_flagged_critical_specifically():
    baseline = _load("rugpull", "v1")
    current = _load("rugpull", "v2")
    report = compare(baseline, current)
    assert report.has_critical
    escalations = [f for f in report.findings if f.kind == "capability_escalation"]
    assert len(escalations) == 1
    assert "network" in escalations[0].details or "data-egress" in escalations[0].details
