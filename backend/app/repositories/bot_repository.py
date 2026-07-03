"""Repository interface for bot-facing data."""

from typing import Protocol

from shared.models import OfficeStatus, Room, Usage


class BotRepository(Protocol):
    """Data access contract used by bot services."""

    async def get_status(self) -> OfficeStatus:
        """Return current office status."""

    async def get_room(self, room_name: str) -> Room | None:
        """Return a room by name, or None when unknown."""

    async def get_usage(self) -> Usage:
        """Return energy usage summary."""
