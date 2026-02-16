"""Public package interface for logtracer."""

from .config import configure
from .decorators import trace_node
from .tracer import trace

__all__ = ["configure", "trace", "trace_node"]
