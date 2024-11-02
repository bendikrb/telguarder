"""Tests for TelguarderClient."""

from __future__ import annotations

import asyncio
import logging
import socket
from unittest.mock import AsyncMock, patch

import aiohttp
from aiohttp.web_response import json_response
from aresponses import ResponsesMockServer
import pytest
from yarl import URL

from telguarder import TelguarderClient
from telguarder.const import LOOKUP_URI, TELGUARDER_API_URL
from telguarder.exceptions import (
    TelguarderConnectionError,
    TelguarderConnectionTimeoutError,
    TelguarderError,
    TelguarderNotFoundError,
    TelguarderUnauthorizedError,
)
from telguarder.models import (
    LookupResult,
    LookupResults,
)

from .helpers import (
    load_fixture_json,
)

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)


@pytest.mark.parametrize(
    "phone_number",
    [
        "48841651",
        ["87654321", "87654321"],
    ],
)
async def test_lookup_number(aresponses: ResponsesMockServer, phone_number):
    fixture = load_fixture_json("nospam") if isinstance(phone_number, list) else load_fixture_json("spam")
    aresponses.add(
        URL(TELGUARDER_API_URL).host,
        LOOKUP_URI,
        "POST",
        json_response(data=fixture),
        repeat=2,
    )

    async with TelguarderClient() as client:
        result = await client.lookup(phone_number)
        assert isinstance(result, LookupResults)
        assert all(isinstance(item, LookupResult) for item in result.results)


async def test_with_params(aresponses: ResponsesMockServer):
    """Test request using params."""
    aresponses.add(
        URL(TELGUARDER_API_URL).host,
        "/params?debug=1",
        "GET",
        json_response(data={"message": "OK"}),
        match_querystring=True,
    )
    async with TelguarderClient() as client:
        assert await client._request("/params", params={"debug": 1})


async def test_timeout(aresponses: ResponsesMockServer):
    """Test request timeout."""

    # Faking a timeout by sleeping
    async def response_handler(_: aiohttp.ClientResponse):
        """Response handler for this test."""
        await asyncio.sleep(2)
        return aresponses.Response(body="Helluu")  # pragma: no cover

    aresponses.add(
        URL(TELGUARDER_API_URL).host,
        LOOKUP_URI,
        "GET",
        response_handler,
    )
    async with TelguarderClient() as client:
        client.request_timeout = 1
        with pytest.raises((TelguarderConnectionError, TelguarderConnectionTimeoutError)):
            assert await client._request(LOOKUP_URI)


async def test_http_error400(aresponses: ResponsesMockServer):
    """Test HTTP 400 response handling."""
    aresponses.add(
        URL(TELGUARDER_API_URL).host,
        LOOKUP_URI,
        "GET",
        aresponses.Response(text="Wtf", status=400),
    )
    async with TelguarderClient() as client:
        with pytest.raises(TelguarderError):
            assert await client._request(LOOKUP_URI)


async def test_http_error401(aresponses: ResponsesMockServer):
    """Test HTTP 401 response handling."""
    aresponses.add(
        URL(TELGUARDER_API_URL).host,
        LOOKUP_URI,
        "GET",
        aresponses.Response(status=401),
    )
    async with TelguarderClient() as client:
        with pytest.raises(TelguarderUnauthorizedError):
            assert await client._request(LOOKUP_URI)


async def test_http_error404(aresponses: ResponsesMockServer):
    """Test HTTP 404 response handling."""
    aresponses.add(
        URL(TELGUARDER_API_URL).host,
        LOOKUP_URI,
        "GET",
        aresponses.Response(text="Not found", status=404),
    )

    async with TelguarderClient() as client:
        with pytest.raises(TelguarderNotFoundError):
            assert await client._request(LOOKUP_URI)


async def test_json_error(aresponses: ResponsesMockServer):
    """Test unexpected error handling."""
    aresponses.add(
        URL(TELGUARDER_API_URL).host,
        LOOKUP_URI,
        "GET",
        json_response(data={"message": "Error", "code": 418}, status=500),
    )

    async with TelguarderClient() as client:
        with pytest.raises(TelguarderError):
            assert await client._request(LOOKUP_URI)


async def test_network_error():
    """Test network error handling."""
    async with TelguarderClient() as client:
        client.session = AsyncMock(spec=aiohttp.ClientSession)
        with patch.object(client.session, "request", side_effect=socket.gaierror), pytest.raises(
            TelguarderConnectionError
        ):
            assert await client._request(LOOKUP_URI)


async def test_unexpected_error(aresponses: ResponsesMockServer):
    """Test unexpected error handling."""
    aresponses.add(
        URL(TELGUARDER_API_URL).host,
        LOOKUP_URI,
        "GET",
        aresponses.Response(text="Error"),
    )

    async with TelguarderClient() as client:
        with pytest.raises(TelguarderError):
            assert await client._request(LOOKUP_URI)


async def test_session_close():
    client = TelguarderClient()
    client.session = AsyncMock(spec=aiohttp.ClientSession)
    client._close_session = True  # pylint: disable=protected-access
    await client.close()
    client.session.close.assert_called_once()


async def test_context_manager():
    async with TelguarderClient() as client:
        assert isinstance(client, TelguarderClient)
    assert client.session is None or client.session.closed
