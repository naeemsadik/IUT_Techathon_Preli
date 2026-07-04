"""Discord message formatting tests."""

from bot.commands.formatting import format_room, format_status, format_usage
from iut_server.app.repositories.mock_repository import MockBotRepository


async def test_format_status_is_human_readable() -> None:
    status = await MockBotRepository().get_status()

    message = format_status(status)

    assert "**Office Status**" in message
    assert "Total Power: 1430W" in message
    assert "Drawing Room" in message
    assert "Fan ON" in message


async def test_format_room_is_human_readable() -> None:
    room = await MockBotRepository().get_room("Work Room 2")
    assert room is not None

    message = format_room(room)

    assert "**Work Room 2**" in message
    assert "Light ON" in message


async def test_format_usage_is_human_readable() -> None:
    usage = await MockBotRepository().get_usage()

    message = format_usage(usage)

    assert "Daily: 18.4 kWh" in message
    assert "Drawing Room: 10.8 kWh" in message
