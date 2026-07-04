"""WebSocket endpoints."""

import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)
router = APIRouter(tags=["websocket"])


@router.websocket("/ws/alerts")
async def alerts(websocket: WebSocket) -> None:
    """Stream real alerts to a connected client."""

    manager = websocket.app.state.alert_ws
    await manager.connect(websocket)
    try:
        await manager.keep_alive(websocket)
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected: /ws/alerts")
    finally:
        await manager.disconnect(websocket)


@router.websocket("/ws/live")
async def live_state(websocket: WebSocket) -> None:
    """Stream hot-state diffs to frontend clients."""

    manager = websocket.app.state.live_state_ws
    await manager.connect(websocket)
    try:
        await manager.keep_alive(websocket)
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected: /ws/live")
    finally:
        await manager.disconnect(websocket)
