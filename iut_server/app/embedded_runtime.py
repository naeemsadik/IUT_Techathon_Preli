"""Optional background runtimes started with the FastAPI server."""

from __future__ import annotations

import argparse
import asyncio
import logging
import os
from typing import Any

from simulator.simulator import run as run_simulator

logger = logging.getLogger(__name__)


def _env_enabled(name: str) -> bool:
    return os.getenv(name, "false").lower() in {"1", "true", "yes", "on"}


def _env_float(name: str, default: float) -> float:
    raw = os.getenv(name)
    return float(raw) if raw else default


def _env_int(name: str, default: int | None = None) -> int | None:
    raw = os.getenv(name)
    return int(raw) if raw else default


def _simulator_args() -> argparse.Namespace:
    return argparse.Namespace(
        url=os.getenv("SIMULATOR_API_URL", os.getenv("API_BASE_URL", "http://127.0.0.1:8000")),
        probability=_env_float("SIMULATOR_TOGGLE_PROB", 0.2),
        room=os.getenv("SIMULATOR_ROOM") or None,
        seed=_env_int("SIMULATOR_SEED"),
    )


def start_embedded_simulator() -> asyncio.Task[None] | None:
    """Start the simulator loop when ENABLE_SIMULATOR is enabled."""

    if not _env_enabled("ENABLE_SIMULATOR"):
        return None

    args = _simulator_args()
    logger.info("Starting embedded simulator against %s", args.url)
    return asyncio.create_task(run_simulator(args), name="embedded-simulator")


def start_embedded_discord_bot() -> tuple[Any, asyncio.Task[None]] | None:
    """Start the Discord bot when ENABLE_DISCORD_BOT is enabled."""

    if not _env_enabled("ENABLE_DISCORD_BOT"):
        return None

    try:
        from bot.bot import create_bot
        from bot.config import get_settings as get_bot_settings
    except ModuleNotFoundError as exc:
        logger.warning("Discord bot dependencies are unavailable; bot disabled: %s", exc)
        return None

    settings = get_bot_settings()
    if not settings.discord_token:
        logger.warning("ENABLE_DISCORD_BOT=true but DISCORD_TOKEN is missing; bot disabled")
        return None

    discord_bot = create_bot()
    logger.info("Starting embedded Discord bot")
    task = asyncio.create_task(
        discord_bot.start(settings.discord_token),
        name="embedded-discord-bot",
    )
    return discord_bot, task
