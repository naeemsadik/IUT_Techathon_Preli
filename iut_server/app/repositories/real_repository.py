"""SQLite-backed repository for bot-facing API operations."""

from __future__ import annotations

from collections import defaultdict
from datetime import UTC, datetime, timedelta

from iut_server.app.persistence.database import Database
from iut_server.app.state import ROOM_SLUGS, HotStateStore
from shared.models import OfficeStatus, Room, RoomUsage, Usage


class RealBotRepository:
    """Reads hot state and computes usage from SQLite cold state."""

    def __init__(self, hot_store: HotStateStore, database: Database) -> None:
        self._hot_store = hot_store
        self._database = database

    async def get_status(self) -> OfficeStatus:
        """Return current office status from hot state."""

        return self._hot_store.get_office_status()

    async def get_room(self, room_name: str) -> Room | None:
        """Return a room by display name or slug."""

        return self._hot_store.get_room(room_name)

    async def get_usage(self) -> Usage:
        """Return energy usage computed from the transition log."""

        now = datetime.now(UTC)
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        week_start = now - timedelta(days=7)
        day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

        transitions = self._database.query_transitions_since(month_start)
        if not transitions:
            return Usage(
                daily_kwh=0.0,
                weekly_kwh=0.0,
                monthly_kwh=0.0,
                per_room=[
                    RoomUsage(room_name=display, kwh=0.0)
                    for display in ROOM_SLUGS.values()
                ],
            )

        by_device: dict[str, list] = defaultdict(list)
        for row in transitions:
            by_device[row.device_id].append(row)

        daily_kwh = 0.0
        weekly_kwh = 0.0
        monthly_kwh = 0.0
        daily_by_room: dict[str, float] = defaultdict(float)
        weekly_by_room: dict[str, float] = defaultdict(float)
        monthly_by_room: dict[str, float] = defaultdict(float)

        for device_id, rows in by_device.items():
            segments = self._build_segments(rows, now)
            for segment_start, segment_end, room, status, power_draw_w in segments:
                if status != "on":
                    continue
                hours = (segment_end - segment_start).total_seconds() / 3600
                kwh = power_draw_w * hours / 1000
                monthly_kwh += kwh
                monthly_by_room[room] += kwh
                if segment_end > week_start and segment_start < now:
                    overlap_start = max(segment_start, week_start)
                    overlap_end = min(segment_end, now)
                    overlap_hours = (overlap_end - overlap_start).total_seconds() / 3600
                    weekly_kwh += power_draw_w * overlap_hours / 1000
                    weekly_by_room[room] += power_draw_w * overlap_hours / 1000
                if segment_end > day_start and segment_start < now:
                    overlap_start = max(segment_start, day_start)
                    overlap_end = min(segment_end, now)
                    overlap_hours = (overlap_end - overlap_start).total_seconds() / 3600
                    daily_kwh += power_draw_w * overlap_hours / 1000
                    daily_by_room[room] += power_draw_w * overlap_hours / 1000

        per_room = [
            RoomUsage(
                room_name=ROOM_SLUGS[room_slug],
                kwh=round(daily_by_room.get(room_slug, 0.0), 3),
            )
            for room_slug in ROOM_SLUGS
        ]

        return Usage(
            daily_kwh=round(daily_kwh, 3),
            weekly_kwh=round(weekly_kwh, 3),
            monthly_kwh=round(monthly_kwh, 3),
            per_room=per_room,
        )

    def _build_segments(self, rows: list, now: datetime) -> list[tuple]:
        """Convert transition rows into contiguous ON/OFF segments."""

        segments: list[tuple] = []
        for index, row in enumerate(rows):
            segment_end = rows[index + 1].recorded_at if index + 1 < len(rows) else now
            segments.append(
                (
                    row.recorded_at,
                    segment_end,
                    row.room,
                    row.status,
                    row.power_draw_w,
                )
            )
        return segments
