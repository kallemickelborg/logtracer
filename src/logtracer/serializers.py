"""Serialization helpers for trace graphs."""

from __future__ import annotations

import json
from pathlib import Path

from .graph import TraceGraph


def trace_to_json(trace: TraceGraph, *, indent: int | None = 2) -> str:
    """Serialize a trace to JSON text."""
    return trace.model_dump_json(indent=indent)


def trace_from_json(payload: str) -> TraceGraph:
    """Deserialize JSON text into a TraceGraph."""
    return TraceGraph.model_validate_json(payload)


def save_trace_json(trace: TraceGraph, path: str | Path, *, indent: int | None = 2) -> Path:
    """Persist a trace as UTF-8 JSON file."""
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(trace_to_json(trace, indent=indent), encoding="utf-8")
    return output_path


def load_trace_json(path: str | Path) -> TraceGraph:
    """Load a trace from a UTF-8 JSON file."""
    payload = Path(path).read_text(encoding="utf-8")
    # Validate as raw JSON first for clearer parse errors.
    json.loads(payload)
    return trace_from_json(payload)
