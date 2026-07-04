"""FastAPI dependency providers."""

from fastapi import Request

from backend.app.alerts import AlertEngine
from backend.app.config import BackendSettings, get_settings
from backend.app.persistence.database import Database
from backend.app.repositories.bot_repository import BotRepository
from backend.app.repositories.real_repository import RealBotRepository
from backend.app.services.bot_service import BotService
from backend.app.state import HotStateStore
from backend.app.websocket.dashboard import DashboardWebSocketManager
from backend.app.websocket.manager import AlertWebSocketManager


def get_hot_store(request: Request) -> HotStateStore:
    """Return the application hot state store."""

    return request.app.state.hot_store


def get_database(request: Request) -> Database:
    """Return the application database."""

    return request.app.state.db


def get_alert_ws(request: Request) -> AlertWebSocketManager:
    """Return the alert WebSocket manager."""

    return request.app.state.alert_ws


def get_dashboard_ws(request: Request) -> DashboardWebSocketManager:
    """Return the dashboard WebSocket manager."""

    return request.app.state.dashboard_ws


def get_alert_engine(request: Request) -> AlertEngine:
    """Return the alert engine."""

    return request.app.state.alert_engine


def get_bot_repository(request: Request) -> BotRepository:
    """Provide the active bot repository implementation."""

    return RealBotRepository(
        hot_store=request.app.state.hot_store,
        database=request.app.state.db,
    )


def get_bot_service(request: Request) -> BotService:
    """Provide the bot service."""

    return BotService(
        repository=get_bot_repository(request),
        settings=get_settings(),
    )
