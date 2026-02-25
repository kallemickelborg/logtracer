"""Instrumentation for the httpx library (sync + async)."""

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


def instrument_httpx(
    *,
    url_filter: Callable[[str], str] | None = None,
    exclude_urls: list[str] | None = None,
) -> None:
    """Patch httpx.Client and httpx.AsyncClient request to create spans when a trace is active."""
    try:
        import httpx
    except ImportError:
        warnings.warn(
            "nodetracer: httpx not installed. Run pip install nodetracer[http].",
            stacklevel=2,
        )
        return

    _patch_client(httpx.Client, url_filter, exclude_urls, sync=True)
    _patch_client(httpx.AsyncClient, url_filter, exclude_urls, sync=False)


def _patch_client(
    client_class: type,
    url_filter: Callable[[str], str] | None,
    exclude_urls: list[str] | None,
    *,
    sync: bool,
) -> None:
    """Patch a Client or AsyncClient class."""
    _original_request = client_class.request

    def _patched_request_sync(
        self: object,
        method: str,
        url: str | object,
        *args: object,
        **kwargs: object,
    ) -> object:
        url_str = str(url)
        span = create_http_span(
            method,
            url_str,
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

    async def _patched_request_async(
        self: object,
        method: str,
        url: str | object,
        *args: object,
        **kwargs: object,
    ) -> object:
        url_str = str(url)
        span = create_http_span(
            method,
            url_str,
            url_filter=url_filter,
            exclude_urls=exclude_urls,
        )
        if span is None:
            return await _original_request(self, method, url, *args, **kwargs)

        span.__enter__()
        start = time.perf_counter()
        exc_type, exc_val, exc_tb = None, None, None
        try:
            response = await _original_request(self, method, url, *args, **kwargs)
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

    client_class.request = _patched_request_sync if sync else _patched_request_async  # type: ignore[method-assign]
