"""Real-time alert broadcasting and evaluation."""

from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime, time
from uuid import uuid4

from backend.app.config import BackendSettings
from backend.app.persistence.database import Database
from backend.app.state import (
    ROOM_SLUGS,
    DeviceRecord,
    HotStateStore,
    device_display_name,
)
from backend.app.websocket.manager import AlertWebSocketManager
from shared.models import Alert

logger = logging.getLogger(__name__)

ALERT_TYPE_OFF_HOURS = "off_hours"
ALERT_TYPE_ROOM_DURATION = "room_duration"


class AlertEngine:
    """Dual-path alert evaluation with de-duplication."""

    def __init__(
        self,
        hot_store: HotStateStore,
        database: Database,
        alert_ws: AlertWebSocketManager,
        settings: BackendSettings,
    ) -> None:
        self._hot_store = hot_store
        self._database = database
        self._alert_ws = alert_ws
        self._settings = settings

    def is_office_hours(self, now: datetime) -> bool:
        """Return True when the given timestamp falls within office hours."""

        current = now.time()
        start = self._settings.office_start
        end = self._settings.office_end
        return start <= current <= end

    async def evaluate_on_ingest(
        self,
        updated: list[DeviceRecord],
        server_time: datetime,
    ) -> None:
        """Run event-driven checks for changed devices and affected rooms."""

        affected_rooms: set[str] = set()
        for record in updated:
            self._resolve_cleared_conditions(record, server_time)
            if record.status == "on":
                await self._maybe_fire_off_hours_alert(record, server_time)
            affected_rooms.add(record.room)

        for room_slug in affected_rooms:
            await self._maybe_fire_room_duration_alert(room_slug, server_time)

    async def evaluate_all(self, server_time: datetime) -> None:
        """Run a full periodic sweep across all devices and rooms."""

        for device in self._hot_store.all_devices():
            self._resolve_cleared_conditions(device, server_time)
            if device.status == "on":
                await self._maybe_fire_off_hours_alert(device, server_time)

        for room_slug in ROOM_SLUGS:
            await self._maybe_fire_room_duration_alert(room_slug, server_time)

    async def run_periodic_sweep(self) -> None:
        """Background task that evaluates time-based alerts on an interval."""

        interval = self._settings.alert_sweep_interval_seconds
        while True:
            try:
                await asyncio.sleep(interval)
                await self.evaluate_all(datetime.now(UTC))
            except asyncio.CancelledError:
                logger.info("Alert sweep task cancelled")
                raise
            except Exception:
                logger.exception("Alert sweep failed")

    def _resolve_cleared_conditions(
        self,
        record: DeviceRecord,
        server_time: datetime,
    ) -> None:
        """Resolve alerts whose underlying conditions have cleared."""

        if record.status == "off":
            self._database.resolve_alerts(
                ALERT_TYPE_OFF_HOURS,
                record.device_id,
                server_time,
            )
            self._database.resolve_alerts(
                ALERT_TYPE_ROOM_DURATION,
                record.room,
                server_time,
            )
            return

        if self.is_office_hours(server_time):
            self._database.resolve_alerts(
                ALERT_TYPE_OFF_HOURS,
                record.device_id,
                server_time,
            )

        devices = self._hot_store.devices_in_room(record.room)
        if not all(device.status == "on" for device in devices):
            self._database.resolve_alerts(
                ALERT_TYPE_ROOM_DURATION,
                record.room,
                server_time,
            )

    async def _maybe_fire_off_hours_alert(
        self,
        record: DeviceRecord,
        server_time: datetime,
    ) -> None:
        """Fire an off-hours alert when a device is ON outside office hours."""

        if self.is_office_hours(server_time):
            return
        if self._database.has_unresolved_alert(ALERT_TYPE_OFF_HOURS, record.device_id):
            return

        room_name = ROOM_SLUGS[record.room]
        device_name = device_display_name(record)
        message = f"{room_name} {device_name} is ON outside office hours."
        await self._create_and_broadcast(
            alert_type=ALERT_TYPE_OFF_HOURS,
            target=record.device_id,
            message=message,
            server_time=server_time,
        )

    async def _maybe_fire_room_duration_alert(
        self,
        room_slug: str,
        server_time: datetime,
    ) -> None:
        """Fire a room duration alert when all devices have been ON long enough."""

        devices = self._hot_store.devices_in_room(room_slug)
        if not devices or not all(device.status == "on" for device in devices):
            return

        oldest_on_time = min(device.last_changed for device in devices)
        if server_time - oldest_on_time < self._settings.duration_threshold:
            return
        if self._database.has_unresolved_alert(ALERT_TYPE_ROOM_DURATION, room_slug):
            return

        room_name = ROOM_SLUGS[room_slug]
        hours = int(self._settings.duration_threshold.total_seconds() // 3600)
        if hours >= 1:
            duration_label = f"{hours} hour{'s' if hours != 1 else ''}"
        else:
            seconds = int(self._settings.duration_threshold.total_seconds())
            duration_label = f"{seconds} seconds"
        message = (
            f"All devices in {room_name} have been ON for over {duration_label}."
        )
        await self._create_and_broadcast(
            alert_type=ALERT_TYPE_ROOM_DURATION,
            target=room_slug,
            message=message,
            server_time=server_time,
        )

    async def _create_and_broadcast(
        self,
        alert_type: str,
        target: str,
        message: str,
        server_time: datetime,
    ) -> None:
        """Persist and broadcast a new alert."""

        alert_id = str(uuid4())
        severity = "warning"
        self._database.create_alert(
            alert_id=alert_id,
            alert_type=alert_type,
            target=target,
            message=message,
            severity=severity,
            created_at=server_time,
        )
        alert = Alert(
            id=alert_id,
            message=message,
            severity=severity,
            created_at=server_time,
        )
        await self._alert_ws.broadcast_alert(alert)
        logger.info("Alert fired: %s (%s)", alert_type, target)
