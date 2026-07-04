"""WebSocket connection manager for live device state diffs."""

from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime
from typing import Any

from fastapi import WebSocket

from backend.app.state import DeviceRecord

logger = logging.getLogger(__name__)


class LiveStateWebSocketManager:
    """Broadcasts hot-state diffs to live frontend clients."""

    def __init__(self) -> None:
        self._connections: set[WebSocket] = set()
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket) -> None:
        """Accept and register a WebSocket connection."""

        await websocket.accept()
        async with self._lock:
            self._connections.add(websocket)
        logger.info(
            "WebSocket connected: /ws/live (%s clients)",
            len(self._connections),
        )

    async def disconnect(self, websocket: WebSocket) -> None:
        """Remove a WebSocket connection."""

        async with self._lock:
            self._connections.discard(websocket)
        logger.info(
            "WebSocket disconnected: /ws/live (%s clients)",
            len(self._connections),
        )

    async def broadcast_diff(
        self,
        changes: list[DeviceRecord],
        totals: dict[str, Any],
        server_time: datetime | None = None,
    ) -> None:
        """Broadcast a state diff to all connected frontend clients."""

        if not changes:
            return

        payload = {
            "message_type": "state_diff",
            "server_time": (server_time or datetime.now(UTC)).isoformat(),
            "changes": [
                {
                    "device_id": record.device_id,
                    "room": record.room,
                    "device_type": record.device_type,
                    "status": record.status,
                    "power_draw_w": record.power_draw_w,
                    "last_changed": record.last_changed.isoformat(),
                }
                for record in changes
            ],
            "total_wattage": totals["total_wattage"],
            "room_wattage": totals["room_wattage"],
        }

        async with self._lock:
            connections = list(self._connections)

        stale: list[WebSocket] = []
        for websocket in connections:
            try:
                await websocket.send_json(payload)
            except Exception:
                stale.append(websocket)

        for websocket in stale:
            await self.disconnect(websocket)

    async def keep_alive(self, websocket: WebSocket) -> None:
        """Keep a connection open until the client disconnects."""

        try:
            while True:
                await websocket.receive_text()
        except Exception:
            return
