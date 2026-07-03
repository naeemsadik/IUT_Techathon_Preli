"""WebSocket endpoints."""

import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from backend.app.websocket.manager import AlertWebSocketManager

logger = logging.getLogger(__name__)
router = APIRouter(tags=["websocket"])


@router.websocket("/ws/alerts")
async def alerts(websocket: WebSocket) -> None:
    """Stream mock alerts to a connected client."""

    manager = AlertWebSocketManager()
    try:
        await manager.stream_alerts(websocket)
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected: /ws/alerts")
