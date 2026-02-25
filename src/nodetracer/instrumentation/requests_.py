"""Instrumentation for the requests library."""

from __future__ import annotations

import sys
import time
import warnings
from collections.abc import Callable

from .base import (
    create_http_span,
    elapsed_ms,
    record_http_response,
)


def instrument_requests(
    *,
    url_filter: Callable[[str], str] | None = None,
    exclude_urls: list[str] | None = None,
) -> None:
    """Patch requests.Session.request to create spans when a trace is active."""
    try:
        import requests
    except ImportError:
        warnings.warn(
            "nodetracer: requests not installed. Run pip install nodetracer[http].",
            stacklevel=2,
        )
        return

    Session = requests.Session
    _original_request = Session.request

    def _patched_request(
        self: object,
        method: str,
        url: str,
        *args: object,
        **kwargs: object,
    ) -> object:
        span = create_http_span(
            method,
            url,
            url_filter=url_filter,
            exclude_urls=exclude_urls,
        )
        if span is None:
            return _original_request(self, method, url, *args, **kwargs)

        span.__enter__()
        start = time.perf_counter()
        exc_type, exc_val, exc_tb = None, None, None
        try:
            response = _original_request(self, method, url, *args, **kwargs)
            status_code = response.status_code if response is not None else None
            record_http_response(
                span,
                status_code=status_code,
                duration_ms=elapsed_ms(start),
            )
            return response
        except Exception as exc:
            exc_type, exc_val, exc_tb = sys.exc_info()
            record_http_response(
                span,
                duration_ms=elapsed_ms(start),
                error=str(exc),
            )
            raise
        finally:
            span.__exit__(exc_type, exc_val, exc_tb)

    Session.request = _patched_request  # type: ignore[method-assign]
