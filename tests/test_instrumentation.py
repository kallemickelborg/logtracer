"""Tests for HTTP auto-instrumentation."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

pytest.importorskip("requests")

from nodetracer.core import Tracer
from nodetracer.instrumentation import instrument_http, instrument_requests
from nodetracer.storage import MemoryStore


def _mock_response(status_code: int = 200) -> MagicMock:
    resp = MagicMock()
    resp.status_code = status_code
    return resp


def test_instrument_requests_creates_span_when_trace_active() -> None:
    """When a trace is active, requests.get creates an http_request span."""
    with patch("requests.sessions.Session.request", return_value=_mock_response(200)):
        instrument_requests()

        tracer = Tracer(storage=MemoryStore())
        with tracer.trace("http_test") as root:
            import requests

            requests.get("https://example.com/api")

        nodes = list(root.trace.nodes.values())
        http_nodes = [n for n in nodes if n.node_type == "http_request"]
        assert len(http_nodes) == 1
        assert http_nodes[0].input_data.get("method") == "GET"
        assert http_nodes[0].input_data.get("url") == "https://example.com/api"
        assert http_nodes[0].output_data.get("status_code") == 200
        assert "duration_ms" in http_nodes[0].output_data


def test_instrument_requests_no_span_when_no_trace() -> None:
    """When no trace is active, requests run normally without creating spans."""
    with patch("requests.Session.request", return_value=_mock_response(200)):
        instrument_requests()

        import requests

        resp = requests.get("https://example.com/")
        assert resp.status_code == 200


def test_instrument_requests_records_error_on_exception() -> None:
    """Failed requests record error in span output."""
    with patch("requests.Session.request", side_effect=ConnectionError("Connection refused")):
        instrument_requests()

        tracer = Tracer(storage=MemoryStore())
        with tracer.trace("http_error") as root:
            import requests

            with pytest.raises(ConnectionError):
                requests.get("https://example.com/")

        nodes = list(root.trace.nodes.values())
        http_nodes = [n for n in nodes if n.node_type == "http_request"]
        assert len(http_nodes) == 1
        assert http_nodes[0].output_data.get("error") == "Connection refused"
        assert http_nodes[0].status.value == "failed"


def test_instrument_http_calls_instrument_requests() -> None:
    """instrument_http() patches requests when requests=True."""
    with patch("requests.Session.request", return_value=_mock_response(200)):
        instrument_http(requests=True, httpx=False, aiohttp=False)

        tracer = Tracer(storage=MemoryStore())
        with tracer.trace("via_instrument_http") as root:
            import requests

            requests.get("https://example.com/")

        http_nodes = [n for n in root.trace.nodes.values() if n.node_type == "http_request"]
        assert len(http_nodes) == 1


def test_exclude_urls_skips_matching_requests() -> None:
    """Requests matching exclude_urls are not traced."""
    with patch("requests.Session.request", return_value=_mock_response(200)):
        instrument_requests(exclude_urls=[r"https://example\.com/skip"])

        tracer = Tracer(storage=MemoryStore())
        with tracer.trace("exclude_test") as root:
            import requests

            requests.get("https://example.com/skip")
            requests.get("https://example.com/trace")

        http_nodes = [n for n in root.trace.nodes.values() if n.node_type == "http_request"]
        assert len(http_nodes) == 1
        assert "trace" in http_nodes[0].input_data.get("url", "")


def test_instrument_httpx_creates_span_when_trace_active() -> None:
    """When a trace is active, httpx.get creates an http_request span."""
    pytest.importorskip("httpx")
    with patch("httpx._client.Client.request", return_value=_mock_response(200)):
        from nodetracer.instrumentation import instrument_httpx

        instrument_httpx()

        tracer = Tracer(storage=MemoryStore())
        with tracer.trace("httpx_test") as root:
            import httpx

            httpx.get("https://example.com/api")

        http_nodes = [n for n in root.trace.nodes.values() if n.node_type == "http_request"]
        assert len(http_nodes) == 1
        assert http_nodes[0].input_data.get("method") == "GET"


@pytest.mark.asyncio
async def test_instrument_aiohttp_creates_span_when_trace_active() -> None:
    """When a trace is active, aiohttp session.get creates an http_request span."""
    pytest.importorskip("aiohttp")
    from unittest.mock import AsyncMock

    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.__aenter__ = AsyncMock(return_value=mock_resp)
    mock_resp.__aexit__ = AsyncMock(return_value=None)

    with patch(
        "aiohttp.client.ClientSession._request", new_callable=AsyncMock, return_value=mock_resp
    ):
        from nodetracer.instrumentation import instrument_aiohttp

        instrument_aiohttp()

        tracer = Tracer(storage=MemoryStore())
        async with tracer.trace("aiohttp_test") as root:
            import aiohttp

            async with (
                aiohttp.ClientSession() as session,
                session.get("https://example.com/api") as _resp,
            ):
                pass

        http_nodes = [n for n in root.trace.nodes.values() if n.node_type == "http_request"]
        assert len(http_nodes) == 1
        assert http_nodes[0].input_data.get("method") == "GET"
