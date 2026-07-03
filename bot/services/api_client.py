"""Reusable HTTP client for bot commands."""

import logging
from typing import Any, TypeVar

import httpx
from pydantic import ValidationError

from shared.models import APIResponse, OfficeStatus, Room, Usage

logger = logging.getLogger(__name__)
T = TypeVar("T")


class ApiClientError(Exception):
    """Base API client error."""


class ApiNotFoundError(ApiClientError):
    """Raised when an API resource is not found."""


class ApiClient:
    """Typed client for the bot REST API."""

    def __init__(self, base_url: str, timeout_seconds: float = 10.0) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout_seconds
        self._client = httpx.AsyncClient(base_url=self._base_url, timeout=self._timeout)

    async def close(self) -> None:
        """Close the underlying HTTP client."""

        await self._client.aclose()

    async def get_status(self) -> OfficeStatus:
        """Fetch office status."""

        return await self._get_model("/api/status", OfficeStatus)

    async def get_room(self, room_name: str) -> Room:
        """Fetch a room by name."""

        return await self._get_model(f"/api/room/{room_name}", Room)

    async def get_usage(self) -> Usage:
        """Fetch usage summary."""

        return await self._get_model("/api/usage", Usage)

    async def health(self) -> dict[str, Any]:
        """Fetch backend health."""

        return await self._get_data("/api/health")

    async def _get_model(self, path: str, model_type: type[T]) -> T:
        payload = await self._get_data(path)
        try:
            return model_type.model_validate(payload)  # type: ignore[attr-defined]
        except ValidationError as exc:
            logger.exception("Malformed response from %s", path)
            raise ApiClientError("The server returned malformed data.") from exc

    async def _get_data(self, path: str) -> Any:
        try:
            logger.info("REST request: GET %s", path)
            response = await self._client.get(path)
            if response.status_code == 404:
                raise ApiNotFoundError("Requested resource was not found.")
            response.raise_for_status()
            envelope = APIResponse[Any].model_validate(response.json())
            return envelope.data
        except ApiNotFoundError:
            raise
        except (httpx.ConnectError, httpx.TimeoutException) as exc:
            logger.warning("Backend unavailable: %s", exc)
            raise ApiClientError("The backend is offline or timed out.") from exc
        except (httpx.HTTPStatusError, httpx.HTTPError, ValueError, ValidationError) as exc:
            logger.warning("API request failed: %s", exc)
            raise ApiClientError("The backend request failed.") from exc
