"""Storage backend abstractions."""

from __future__ import annotations

from typing import Protocol

from ..graph import TraceGraph


class StorageBackend(Protocol):
    """Protocol for persisting traces."""

    def save(self, trace: TraceGraph) -> None:
        """Persist one trace."""

    def load(self, trace_id: str) -> TraceGraph | None:
        """Return one trace by ID when present."""

    def list_traces(self) -> list[str]:
        """List known trace IDs."""
