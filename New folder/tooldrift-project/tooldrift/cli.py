"""tooldrift command-line interface.

Usage:
    tooldrift snapshot <tools.json> --out baseline.json
    tooldrift check <tools.json> --baseline baseline.json [--json]

Exit codes (designed for CI):
    0 = no drift, or only informational drift
    1 = high-severity drift found (review required, non-fatal in CI if you choose)
    2 = critical drift found (capability escalation -- recommended to fail the build)
"""
from __future__ import annotations

import argparse
import json
import sys

from .diff import compare
from .extractor import load_tools_from_json
from .report import render_text
from .snapshot import load_snapshot, save_snapshot


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="tooldrift")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_snap = sub.add_parser("snapshot", help="Save a tool export as the new trusted baseline")
    p_snap.add_argument("source", help="Path to a JSON tool export (tools/list shaped)")
    p_snap.add_argument("--out", required=True, help="Where to write the baseline snapshot")

    p_check = sub.add_parser("check", help="Compare a tool export against a trusted baseline")
    p_check.add_argument("source", help="Path to a JSON tool export (tools/list shaped)")
    p_check.add_argument("--baseline", required=True, help="Path to the trusted baseline snapshot")
    p_check.add_argument("--json", action="store_true", help="Emit machine-readable JSON report")
    p_check.add_argument(
        "--semantic-threshold",
        type=float,
        default=0.35,
        help=(
            "Similarity below this value counts as semantic drift (default 0.35, "
            "chosen empirically -- see eval/run_eval.py and README for the sweep)"
        ),
    )

    args = parser.parse_args(argv)
    exit_code = 0

    try:
        if args.cmd == "snapshot":
            tools = load_tools_from_json(args.source)
            save_snapshot(tools, args.out)
            print(f"tooldrift: saved trusted baseline with {len(tools)} tool(s) to {args.out}")
            exit_code = 0

        elif args.cmd == "check":
            current = {t.name: t for t in load_tools_from_json(args.source)}
            baseline = load_snapshot(args.baseline)
            report = compare(baseline, current, semantic_threshold=args.semantic_threshold)

            if args.json:
                print(json.dumps(report.to_dict(), indent=2))
            else:
                print(render_text(report))

            if report.has_critical:
                exit_code = 2
            elif report.has_blocking:
                exit_code = 1
            else:
                exit_code = 0
        else:
            parser.print_help()
            exit_code = 1
    finally:
        # Explicit flush: some process-exit paths (notably `sys.exit()` from
        # inside a `python -m` invocation under certain process supervisors)
        # can truncate a fully-buffered stdout before the interpreter's normal
        # atexit flush runs. Flushing here is cheap insurance so CI logs and
        # piped output never silently lose the final report.
        sys.stdout.flush()
        sys.stderr.flush()

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
