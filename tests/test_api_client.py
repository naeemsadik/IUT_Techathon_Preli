"""Bot API client tests."""

import httpx
import pytest

from bot.services.api_client import ApiClient, ApiNotFoundError


def make_client(transport: httpx.MockTransport) -> ApiClient:
    """Create an ApiClient using a mock transport."""

    client = ApiClient("http://testserver")
    client._client = httpx.AsyncClient(transport=transport, base_url="http://testserver")
    return client


@pytest.mark.asyncio
async def test_api_client_parses_status() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "success": True,
                "data": {
                    "office_status": "operational",
                    "total_wattage": 40,
                    "rooms": [
                        {
                            "name": "Work Room 2",
                            "devices": [{"name": "Light", "state": "ON", "wattage": 40}],
                            "total_wattage": 40,
                        }
                    ],
                },
            },
        )

    client = make_client(httpx.MockTransport(handler))

    status = await client.get_status()
    await client.close()

    assert status.total_wattage == 40


@pytest.mark.asyncio
async def test_api_client_raises_not_found() -> None:
    client = make_client(
        httpx.MockTransport(lambda request: httpx.Response(404, json={"detail": "no"}))
    )

    with pytest.raises(ApiNotFoundError):
        await client.get_room("Unknown")
    await client.close()
