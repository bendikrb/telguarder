"""Telguarder API."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from http import HTTPStatus
import logging
import socket
from typing import Self

from aiohttp.client import ClientError, ClientResponse, ClientResponseError, ClientSession
from aiohttp.hdrs import METH_GET, METH_POST
import async_timeout
import orjson
from yarl import URL

from telguarder.const import (
    DEFAULT_REQUEST_TIMEOUT,
    LOOKUP_URI,
    SERVICE_KEY,
    TELGUARDER_API_URL,
)
from telguarder.exceptions import (
    TelguarderConnectionError,
    TelguarderConnectionTimeoutError,
    TelguarderError,
    TelguarderNotFoundError,
    TelguarderUnauthorizedError,
)
from telguarder.models import LookupResults

_LOGGER = logging.getLogger(__name__)


@dataclass
class TelguarderClient:
    """A client for interacting with the Telguarder API."""

    country_code: str = "NO"
    """Country code for the Telguarder service."""
    request_timeout: int = DEFAULT_REQUEST_TIMEOUT
    """Timeout for API requests in seconds."""
    session: ClientSession | None = None
    """(ClientSession | None): The :class:`aiohttp.ClientSession` to use for API requests."""

    _close_session: bool = False

    def _ensure_session(self):
        if self.session is None:
            self.session = ClientSession()
            _LOGGER.debug("New session created.")
            self._close_session = True

    @staticmethod
    async def _request_check_status(response: ClientResponse):
        if response.status == HTTPStatus.NOT_FOUND:
            raise TelguarderNotFoundError("Resource not found")
        if response.status == HTTPStatus.BAD_REQUEST:
            raise TelguarderError("Bad request syntax or unsupported method")
        if response.status == HTTPStatus.UNAUTHORIZED:
            raise TelguarderUnauthorizedError("Unauthorized")
        if response.status != HTTPStatus.OK:
            raise TelguarderError(response)

    async def _request(
        self,
        uri: str,
        method: str = METH_GET,
        **kwargs,
    ) -> str | dict | list | bool | None:
        """Make a request to the Telguarder API.

        Args:
            uri (str): The URI for the API endpoint.
            method (str): The HTTP method to use for the request.
            retry (int): The number of retries for the request.
            **kwargs: Additional keyword arguments for the request.
                May include:
                - params (dict): Query parameters for the request.
                - json (dict): JSON data to send in the request body.
                - headers (dict): Additional headers for the request.

        Returns:
            The response data from the API.

        """
        url = URL(TELGUARDER_API_URL).join(URL(uri))

        headers = {
            **self.request_header,
            **kwargs.get("headers", {}),
        }
        kwargs.update({"headers": headers})

        params = kwargs.get("params")
        if params is not None:
            kwargs.update(params={k: str(v) for k, v in params.items() if v is not None})

        _LOGGER.debug(
            "Executing %s API request to %s.",
            method,
            url.with_query(kwargs.get("params")),
        )
        self._ensure_session()

        try:
            async with async_timeout.timeout(self.request_timeout):
                response = await self.session.request(
                    method,
                    url,
                    **kwargs,
                    raise_for_status=self._request_check_status,
                )
        except asyncio.TimeoutError as exception:
            raise TelguarderConnectionTimeoutError(
                "Timeout occurred while connecting to Telguarder API"
            ) from exception
        except (
            ClientError,
            ClientResponseError,
            socket.gaierror,
        ) as exception:
            msg = f"Error occurred while communicating with Telguarder API: {exception}"
            raise TelguarderConnectionError(msg) from exception

        content_type = response.headers.get("Content-Type", "")
        text = await response.text()
        if "application/json" not in content_type:
            msg = "Unexpected response from the Telguarder API"
            raise TelguarderError(
                msg,
                {"Content-Type": content_type, "response": text},
            )
        return orjson.loads(text)

    @property
    def request_header(self) -> dict[str, str]:
        """Generate a header for HTTP requests to the server."""
        return {
            "Accept": "application/json",
            "X-Country-Code": self.country_code,
            "X-ServiceKey": SERVICE_KEY,
        }

    async def lookup(self, phone_number: list[str] | str) -> LookupResults:
        """Lookup a phone number."""
        if isinstance(phone_number, str):
            phone_number = [phone_number]
        result = await self._request(
            LOOKUP_URI,
            method=METH_POST,
            json={
                "Numbers": phone_number,
            },
        )
        return LookupResults.from_dict(result)

    async def close(self) -> None:
        """Close open client session."""
        if self.session and self._close_session:
            await self.session.close()

    async def __aenter__(self) -> Self:
        """Async enter."""
        return self

    async def __aexit__(self, *_exc_info: object) -> None:
        """Async exit."""
        await self.close()
