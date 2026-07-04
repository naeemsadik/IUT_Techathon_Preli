"""FastAPI application factory."""

import asyncio
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from iut_server.app.alerts import AlertEngine
from iut_server.app.api.bot import router as bot_router
from iut_server.app.api.history import router as history_router
from iut_server.app.api.ingest import router as ingest_router
from iut_server.app.api.websocket import router as websocket_router
from iut_server.app.config import get_settings
from iut_server.app.persistence.database import Database
from iut_server.app.state import HotStateStore
from iut_server.app.websocket.live_state import LiveStateWebSocketManager
from iut_server.app.websocket.manager import AlertWebSocketManager

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Handle application startup and shutdown."""

    settings = get_settings()
    database = Database(settings.sqlite_path)
    database.init_db()
    hot_store = HotStateStore()
    alert_ws = AlertWebSocketManager()
    live_state_ws = LiveStateWebSocketManager()
    alert_engine = AlertEngine(hot_store, database, alert_ws, settings)

    app.state.db = database
    app.state.hot_store = hot_store
    app.state.alert_ws = alert_ws
    app.state.live_state_ws = live_state_ws
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

    # CORS: allow Vercel deployments + local dev hosts.
    # Set CORS_ALLOW_ORIGINS="https://your-app.vercel.app,..."
    # in production. Wildcard "*" is intentionally NOT used so credentials
    # and Authorization headers remain safe.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.cors_allow_origins),
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization"],
    )

    app.include_router(bot_router)
    app.include_router(history_router)
    app.include_router(ingest_router)
    app.include_router(websocket_router)

    return app


app = create_app()
