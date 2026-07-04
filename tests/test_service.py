"""Service layer tests."""

import pytest

from iut_server.app.services.bot_service import BotService, RoomNotFoundError


@pytest.mark.asyncio
async def test_service_returns_room(bot_service: BotService) -> None:
    room = await bot_service.get_room("Work Room 1")

    assert room.total_wattage == 115


@pytest.mark.asyncio
async def test_service_raises_for_unknown_room(bot_service: BotService) -> None:
    with pytest.raises(RoomNotFoundError):
        await bot_service.get_room("Server Room")


def test_service_health_contains_version(bot_service: BotService) -> None:
    health = bot_service.get_health()

    assert health["status"] == "ok"
    assert health["version"] == "0.1.0"
    assert "server_time" in health
