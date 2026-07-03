"""Mock alert stream manager."""

import asyncio
import logging
from datetime import UTC, datetime
from itertools import cycle
from uuid import uuid4

from fastapi import WebSocket

from shared.models import Alert

logger = logging.getLogger(__name__)

ALERT_INTERVAL_SECONDS = 15
MOCK_ALERT_MESSAGES = (
    "Drawing Room lights are still ON.",
    "Work Room 1 exceeds usage threshold.",
    "After-hours usage detected.",
)


class AlertWebSocketManager:
    """Streams rotating mock alerts to connected clients."""

    async def stream_alerts(self, websocket: WebSocket) -> None:
        """Accept a WebSocket and send mock alerts forever."""

        await websocket.accept()
        logger.info("WebSocket connected: /ws/alerts")
        messages = cycle(MOCK_ALERT_MESSAGES)
        while True:
            alert = Alert(
                id=str(uuid4()),
                message=next(messages),
                severity="warning",
                created_at=datetime.now(UTC),
            )
            await websocket.send_json(alert.model_dump(mode="json"))
            await asyncio.sleep(ALERT_INTERVAL_SECONDS)
