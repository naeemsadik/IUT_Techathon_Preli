"""FastAPI dependency providers."""

from backend.app.repositories.bot_repository import BotRepository
from backend.app.repositories.mock_repository import MockBotRepository
from backend.app.services.bot_service import BotService


def get_bot_repository() -> BotRepository:
    """Provide the active bot repository implementation."""

    return MockBotRepository()


def get_bot_service() -> BotService:
    """Provide the bot service."""

    return BotService(repository=get_bot_repository())
