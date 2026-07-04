"""Repository tests."""

import pytest

from iut_server.app.repositories.mock_repository import MockBotRepository


@pytest.mark.asyncio
async def test_mock_repository_returns_status() -> None:
    repository = MockBotRepository()

    status = await repository.get_status()

    assert status.total_wattage == 1430
    assert [room.name for room in status.rooms] == [
        "Drawing Room",
        "Work Room 1",
        "Work Room 2",
    ]


@pytest.mark.asyncio
async def test_mock_repository_room_lookup_is_case_insensitive() -> None:
    repository = MockBotRepository()

    room = await repository.get_room("drawing room")

    assert room is not None
    assert room.name == "Drawing Room"


@pytest.mark.asyncio
async def test_mock_repository_returns_usage() -> None:
    repository = MockBotRepository()

    usage = await repository.get_usage()

    assert usage.daily_kwh == 18.4
    assert len(usage.per_room) == 3
