"""Context propagation primitives for traces and nodes."""

from __future__ import annotations

import contextvars
from collections.abc import Callable
from typing import ParamSpec, TypeVar

from .graph import Node, TraceGraph

P = ParamSpec("P")
R = TypeVar("R")

_current_trace: contextvars.ContextVar[TraceGraph | None] = contextvars.ContextVar(
    "logtracer_current_trace",
    default=None,
)
_current_node: contextvars.ContextVar[Node | None] = contextvars.ContextVar(
    "logtracer_current_node",
    default=None,
)


def get_current_trace() -> TraceGraph | None:
    """Return the active trace for this execution context."""
    return _current_trace.get()


def get_current_node() -> Node | None:
    """Return the active node for this execution context."""
    return _current_node.get()


def push_current_trace(trace: TraceGraph) -> contextvars.Token[TraceGraph | None]:
    """Set and tokenise the active trace."""
    return _current_trace.set(trace)


def push_current_node(node: Node | None) -> contextvars.Token[Node | None]:
    """Set and tokenise the active node."""
    return _current_node.set(node)


def reset_current_trace(token: contextvars.Token[TraceGraph | None]) -> None:
    """Restore a prior trace context."""
    _current_trace.reset(token)


def reset_current_node(token: contextvars.Token[Node | None]) -> None:
    """Restore a prior node context."""
    _current_node.reset(token)


def clear_context() -> None:
    """Clear trace and node from the current context."""
    _current_trace.set(None)
    _current_node.set(None)


def propagate_context(func: Callable[P, R]) -> Callable[P, R]:
    """Copy contextvars to a callable for thread execution."""
    copied_context = contextvars.copy_context()

    def wrapped(*args: P.args, **kwargs: P.kwargs) -> R:
        return copied_context.run(func, *args, **kwargs)

    return wrapped
