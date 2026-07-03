"""Service layer for bot-facing API operations."""

from datetime import UTC, datetime

from backend.app.config import BackendSettings, get_settings
from backend.app.repositories.bot_repository import BotRepository
from shared.models import OfficeStatus, Room, Usage


class RoomNotFoundError(Exception):
    """Raised when a requested room does not exist."""


class BotService:
    """Coordinates bot-facing repository access."""

    def __init__(
        self,
        repository: BotRepository,
        settings: BackendSettings | None = None,
    ) -> None:
        self._repository = repository
        self._settings = settings or get_settings()

    async def get_status(self) -> OfficeStatus:
        """Return current office status."""

        return await self._repository.get_status()

    async def get_room(self, room_name: str) -> Room:
        """Return a room or raise when it is unknown."""

        room = await self._repository.get_room(room_name)
        if room is None:
            raise RoomNotFoundError(f"Unknown room: {room_name}")
        return room

    async def get_usage(self) -> Usage:
        """Return usage summary."""

        return await self._repository.get_usage()

    def get_health(self) -> dict[str, str]:
        """Return service health metadata."""

        return {
            "status": "ok",
            "version": self._settings.version,
            "server_time": datetime.now(UTC).isoformat(),
        }
