"""WebSocket connection manager for real alert broadcasts."""

from __future__ import annotations

import asyncio
import logging

from fastapi import WebSocket

from shared.models import Alert

logger = logging.getLogger(__name__)


class AlertWebSocketManager:
    """Broadcasts real alerts to all connected clients."""

    def __init__(self) -> None:
        self._connections: set[WebSocket] = set()
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket) -> None:
        """Accept and register a WebSocket connection."""

        await websocket.accept()
        async with self._lock:
            self._connections.add(websocket)
        logger.info("WebSocket connected: /ws/alerts (%s clients)", len(self._connections))

    async def disconnect(self, websocket: WebSocket) -> None:
        """Remove a WebSocket connection."""

        async with self._lock:
            self._connections.discard(websocket)
        logger.info(
            "WebSocket disconnected: /ws/alerts (%s clients)",
            len(self._connections),
        )

    async def broadcast_alert(self, alert: Alert) -> None:
        """Send an alert to all connected clients."""

        payload = alert.model_dump(mode="json")
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
