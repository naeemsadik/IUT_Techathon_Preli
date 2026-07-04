"""Shared test fixtures."""

import pytest
from fastapi.testclient import TestClient

from iut_server.app.dependencies import get_bot_service
from iut_server.app.main import create_app
from iut_server.app.repositories.mock_repository import MockBotRepository
from iut_server.app.services.bot_service import BotService


@pytest.fixture
def bot_service() -> BotService:
    """Return a service backed by the mock repository."""

    return BotService(repository=MockBotRepository())


@pytest.fixture
def api_client(bot_service: BotService) -> TestClient:
    """Return a FastAPI test client with explicit dependency overrides."""

    app = create_app()
    app.dependency_overrides[get_bot_service] = lambda: bot_service
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()
