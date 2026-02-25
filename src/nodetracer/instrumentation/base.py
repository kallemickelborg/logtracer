"""Shared logic for HTTP instrumentation."""

from __future__ import annotations

import re
import time
import warnings
from collections.abc import Callable

from ..core.context import get_current_trace
from ..core.span import Span
from ..models import NodeStatus


def _span_name(method: str, url: str) -> str:
    """Generate a span name from HTTP method and URL."""
    return f"{method.upper()} {url}"


def _should_skip(url: str, exclude_urls: list[str] | None) -> bool:
    """Return True if the URL matches any exclude pattern."""
    if not exclude_urls:
        return False
    for pattern in exclude_urls:
        try:
            if re.search(pattern, url):
                return True
        except re.error:
            continue
    return False


def _apply_url_filter(url: str, url_filter: Callable[[str], str] | None) -> str:
    """Apply optional URL filter for redaction."""
    if url_filter is None:
        return url
    try:
        return url_filter(url)
    except Exception:
        return url


def create_http_span(
    method: str,
    url: str,
    *,
    url_filter: Callable[[str], str] | None = None,
    exclude_urls: list[str] | None = None,
) -> Span | None:
    """Create an HTTP span if a trace is active. Returns None if no trace."""
    trace = get_current_trace()
    if trace is None:
        return None

    filtered_url = _apply_url_filter(url, url_filter)
    if _should_skip(filtered_url, exclude_urls):
        return None

    name = _span_name(method, filtered_url)
    span = Span(
        trace=trace,
        name=name,
        node_type="http_request",
    )
    span.input(method=method.upper(), url=filtered_url)
    return span


def record_http_response(
    span: Span,
    *,
    status_code: int | None = None,
    duration_ms: float,
    error: str | None = None,
) -> None:
    """Record HTTP response data on the span."""
    try:
        output: dict[str, object] = {"duration_ms": round(duration_ms, 2)}
        if status_code is not None:
            output["status_code"] = status_code
        if error is not None:
            output["error"] = error
            span.set_status(NodeStatus.FAILED)
        span.output(**output)
    except Exception:
        warnings.warn(
            "nodetracer: failed to record HTTP response on span",
            stacklevel=2,
        )


def elapsed_ms(start: float) -> float:
    """Return elapsed milliseconds since start (from time.perf_counter())."""
    return (time.perf_counter() - start) * 1000.0
