"""Command line interface for logtracer."""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
from typing import Literal, cast

from .console import render_trace
from .serializers import load_trace_json

VerbosityArg = Literal["minimal", "standard", "full"]


def build_parser() -> argparse.ArgumentParser:
    """Build the root CLI parser."""
    parser = argparse.ArgumentParser(prog="logtracer")
    subparsers = parser.add_subparsers(dest="command", required=True)

    inspect_parser = subparsers.add_parser("inspect", help="Inspect a trace JSON file")
    inspect_parser.add_argument("trace_file", type=Path, help="Path to trace JSON file")
    inspect_parser.add_argument(
        "--verbosity",
        choices=["minimal", "standard", "full"],
        default="standard",
        help="Console render verbosity",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Execute the CLI."""
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "inspect":
        return _run_inspect(args.trace_file, cast(VerbosityArg, args.verbosity))

    parser.error("Unknown command")
    return 2


def _run_inspect(trace_file: Path, verbosity: VerbosityArg) -> int:
    """Inspect a trace file and print summary + tree."""
    trace = load_trace_json(trace_file)
    status_counts = Counter(node.status for node in trace.nodes.values())
    type_counts = Counter(node.node_type for node in trace.nodes.values())
    duration = f"{trace.duration_ms:.0f}ms" if trace.duration_ms is not None else "unknown"

    print(f"Trace ID: {trace.trace_id}")
    print(f"Name: {trace.name or '<unnamed>'}")
    print(f"Schema: {trace.schema_version}")
    print(f"Duration: {duration}")
    print(f"Nodes: {len(trace.nodes)}")
    print(f"Edges: {len(trace.edges)}")
    print("Status counts:")
    for status, count in sorted(status_counts.items(), key=lambda item: item[0].value):
        print(f"  - {status.value}: {count}")
    print("Node type counts:")
    for node_type, count in sorted(type_counts.items(), key=lambda item: item[0]):
        print(f"  - {node_type}: {count}")
    print()
    print(render_trace(trace, verbosity=verbosity))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
