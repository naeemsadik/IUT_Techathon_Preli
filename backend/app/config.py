"""Backend configuration."""

import os
from dataclasses import dataclass
from datetime import time, timedelta
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")


def _parse_time(value: str) -> time:
    """Parse HH:MM or HH:MM:SS into a time object."""

    parts = value.split(":")
    hour = int(parts[0])
    minute = int(parts[1]) if len(parts) > 1 else 0
    second = int(parts[2]) if len(parts) > 2 else 0
    return time(hour, minute, second)


@dataclass(frozen=True)
class BackendSettings:
    """Settings loaded from environment variables."""

    host: str
    port: int
    debug: bool
    version: str
    office_start: time
    office_end: time
    duration_threshold: timedelta
    device_duration_threshold: timedelta
    sqlite_path: str
    alert_sweep_interval_seconds: int
    cors_allow_origins: tuple[str, ...]


@lru_cache
def get_settings() -> BackendSettings:
    """Return cached backend settings."""

    def _parse_duration(value: str, default: int) -> timedelta:
        """Parse a non-negative integer seconds value, falling back to default."""

        try:
            seconds = int(value)
        except (TypeError, ValueError):
            return timedelta(seconds=default)
        if seconds < 0:
            return timedelta(seconds=default)
        return timedelta(seconds=seconds)

    def _parse_csv(value: str | None) -> tuple[str, ...]:
        if not value:
            return ()
        return tuple(
            origin.strip() for origin in value.split(",") if origin.strip()
        )

    raw_cors = os.getenv("CORS_ALLOW_ORIGINS", "")
    cors_origins = _parse_csv(raw_cors)
    if not cors_origins:
        # Sensible development defaults; Vercel preview URLs are covered by
        # CORS_ALLOW_ORIGINS in production.
        cors_origins = (
            "http://localhost:3000",
            "http://127.0.0.1:3000",
        )

    return BackendSettings(
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "8000")),
        debug=os.getenv("DEBUG", "false").lower() in {"1", "true", "yes", "on"},
        version="0.1.0",
        office_start=_parse_time(os.getenv("OFFICE_START", "09:00")),
        office_end=_parse_time(os.getenv("OFFICE_END", "17:00")),
        duration_threshold=_parse_duration(
            os.getenv("DURATION_THRESHOLD_SECONDS"), 7200
        ),
        device_duration_threshold=_parse_duration(
            os.getenv("DEVICE_DURATION_THRESHOLD_SECONDS"), 3600
        ),
        sqlite_path=os.getenv("SQLITE_PATH", "data/office_energy.db"),
        alert_sweep_interval_seconds=int(
            os.getenv("ALERT_SWEEP_INTERVAL_SECONDS", "30")
        ),
        cors_allow_origins=cors_origins,
    )
