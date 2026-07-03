"""Discord bot configuration."""

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")


@dataclass(frozen=True)
class BotSettings:
    """Settings loaded from bot environment variables."""

    discord_token: str
    api_base_url: str
    alert_channel_id: int | None
    command_prefix: str
    groq_api_key: str
    groq_model: str
    llm_enabled: bool


@lru_cache
def get_settings() -> BotSettings:
    """Return cached bot settings."""

    channel_id = os.getenv("ALERT_CHANNEL_ID")
    return BotSettings(
        discord_token=os.getenv("DISCORD_TOKEN", ""),
        api_base_url=os.getenv("API_BASE_URL", "http://127.0.0.1:8000"),
        alert_channel_id=int(channel_id) if channel_id else None,
        command_prefix=os.getenv("COMMAND_PREFIX", "!"),
        groq_api_key=os.getenv("GROQ_API_KEY", ""),
        groq_model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
        llm_enabled=os.getenv("LLM_ENABLED", "true").lower()
        in {"1", "true", "yes", "on"},
    )
