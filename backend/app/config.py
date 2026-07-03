"""Backend configuration."""

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")


@dataclass(frozen=True)
class BackendSettings:
    """Settings loaded from environment variables."""

    host: str
    port: int
    debug: bool
    version: str


@lru_cache
def get_settings() -> BackendSettings:
    """Return cached backend settings."""

    return BackendSettings(
        host=os.getenv("HOST", "127.0.0.1"),
        port=int(os.getenv("PORT", "8000")),
        debug=os.getenv("DEBUG", "false").lower() in {"1", "true", "yes", "on"},
        version="0.1.0",
    )
