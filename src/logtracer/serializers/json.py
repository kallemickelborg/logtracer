"""JSON serialization helpers for trace graphs."""

from __future__ import annotations

import json
from pathlib import Path

from ..models import TraceGraph


def trace_to_json(trace: TraceGraph, *, indent: int | None = 2) -> str:
    return trace.model_dump_json(indent=indent)


def trace_from_json(payload: str) -> TraceGraph:
    return TraceGraph.model_validate_json(payload)


def save_trace_json(trace: TraceGraph, path: str | Path, *, indent: int | None = 2) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(trace_to_json(trace, indent=indent), encoding="utf-8")
    return output_path


def load_trace_json(path: str | Path) -> TraceGraph:
    payload = Path(path).read_text(encoding="utf-8")
    json.loads(payload)
    return trace_from_json(payload)
