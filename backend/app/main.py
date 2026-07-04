"""FastAPI application factory."""

import asyncio
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from backend.app.alerts import AlertEngine
from backend.app.api.bot import router as bot_router
from backend.app.api.ingest import router as ingest_router
from backend.app.api.websocket import router as websocket_router
from backend.app.config import get_settings
from backend.app.persistence.database import Database
from backend.app.state import HotStateStore
from backend.app.websocket.dashboard import DashboardWebSocketManager
from backend.app.websocket.manager import AlertWebSocketManager

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Handle application startup and shutdown."""

    settings = get_settings()
    database = Database(settings.sqlite_path)
    database.init_db()
    hot_store = HotStateStore()
    alert_ws = AlertWebSocketManager()
    dashboard_ws = DashboardWebSocketManager()
    alert_engine = AlertEngine(hot_store, database, alert_ws, settings)

    app.state.db = database
    app.state.hot_store = hot_store
    app.state.alert_ws = alert_ws
    app.state.dashboard_ws = dashboard_ws
    app.state.alert_engine = alert_engine

    sweep_task = asyncio.create_task(alert_engine.run_periodic_sweep())
    logger.info("Server started")
    try:
        yield
    finally:
        sweep_task.cancel()
        try:
            await sweep_task
        except asyncio.CancelledError:
            pass
        database.close()
        logger.info("Server stopped")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""

    settings = get_settings()
    logging.basicConfig(
        level=logging.DEBUG if settings.debug else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s - %(message)s",
    )

    app = FastAPI(
        title="Office Energy Bot API",
        version=settings.version,
        debug=settings.debug,
        lifespan=lifespan,
    )
    app.include_router(bot_router)
    app.include_router(ingest_router)
    app.include_router(websocket_router)

    return app


app = create_app()
