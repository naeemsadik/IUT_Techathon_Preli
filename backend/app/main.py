"""FastAPI application factory."""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from backend.app.api.bot import router as bot_router
from backend.app.api.websocket import router as websocket_router
from backend.app.config import get_settings

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Handle application startup and shutdown."""

    logger.info("Server started")
    yield


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
    app.include_router(websocket_router)

    return app


app = create_app()
