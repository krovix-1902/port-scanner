"""
Evaluation harness.

Runs tooldrift's drift detector across every labeled fixture pair in
tests/fixtures/ and reports precision/recall/accuracy for whether the
tool correctly predicts "should this block CI" -- across a sweep of
semantic-similarity thresholds, so the default threshold in
tooldrift/diff.py is chosen empirically instead of guessed.

Honest limitation (stated here and in the README): this is a small,
hand-curated fixture set (n=4 pairs: benign, rug-pull, adversarial
reword, tool swap), not a large real-world corpus. It's enough to
demonstrate the method and catch regressions, but a production
deployment should grow this set from real MCP server version history.
"""
from __future__ import annotations

import json
from pathlib import Path

from tooldrift.diff import compare
from tooldrift.extractor import load_tools_from_json

FIXTURES = Path(__file__).parent.parent / "tests" / "fixtures"
LABELS = json.loads((FIXTURES / "labels.json").read_text())
CASES = ["benign", "rugpull", "reword", "addremove"]


def _load(name: str, version: str):
    tools = load_tools_from_json(str(FIXTURES / f"{name}_{version}.json"))
    return {t.name: t for t in tools}


def evaluate_at_threshold(threshold: float):
    tp = fp = tn = fn = 0
    rows = []
    for case in CASES:
        baseline = _load(case, "v1")
        current = _load(case, "v2")
        report = compare(baseline, current, semantic_threshold=threshold)
        predicted_blocking = report.has_blocking
        expected_blocking = LABELS[case]["expect_blocking"]

        if predicted_blocking and expected_blocking:
            tp += 1
        elif predicted_blocking and not expected_blocking:
            fp += 1
        elif not predicted_blocking and not expected_blocking:
            tn += 1
        else:
            fn += 1

        rows.append(
            {
                "case": case,
                "expected_blocking": expected_blocking,
                "predicted_blocking": predicted_blocking,
                "correct": predicted_blocking == expected_blocking,
            }
        )

    precision = tp / (tp + fp) if (tp + fp) else float("nan")
    recall = tp / (tp + fn) if (tp + fn) else float("nan")
    accuracy = (tp + tn) / len(CASES)
    return {
        "threshold": threshold,
        "tp": tp,
        "fp": fp,
        "tn": tn,
        "fn": fn,
        "precision": precision,
        "recall": recall,
        "accuracy": accuracy,
        "rows": rows,
    }


def main():
    thresholds = [round(0.05 * i, 2) for i in range(1, 19)]  # 0.05 .. 0.90
    results = [evaluate_at_threshold(t) for t in thresholds]

    print(f"{'thr':>5} {'TP':>3} {'FP':>3} {'TN':>3} {'FN':>3} {'precision':>10} {'recall':>7} {'acc':>5}")
    best = None
    for r in results:
        print(
            f"{r['threshold']:>5} {r['tp']:>3} {r['fp']:>3} {r['tn']:>3} {r['fn']:>3} "
            f"{r['precision']:>10.2f} {r['recall']:>7.2f} {r['accuracy']:>5.2f}"
        )
        # pick the highest threshold that still achieves perfect accuracy
        # (prefer a higher threshold = fewer false positives on benign
        # changes, as long as it doesn't cost recall on real attacks)
        if r["accuracy"] == 1.0:
            best = r

    print()
    if best:
        print(
            f"Recommended default semantic_threshold = {best['threshold']} "
            f"(accuracy=1.00, precision={best['precision']:.2f}, recall={best['recall']:.2f} "
            f"on the {len(CASES)}-case labeled fixture set)"
        )
    else:
        print("No threshold achieved perfect accuracy on this fixture set.")

    Path(Path(__file__).parent / "results.json").write_text(
        json.dumps(results, indent=2)
    )


if __name__ == "__main__":
    main()
