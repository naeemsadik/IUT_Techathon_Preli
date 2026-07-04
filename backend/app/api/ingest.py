"""Ingestion gateway endpoints."""

import logging
from datetime import UTC, datetime
from fastapi import APIRouter, Depends, HTTPException

from backend.app.alerts import AlertEngine
from backend.app.dependencies import (
    get_alert_engine,
    get_dashboard_ws,
    get_database,
    get_hot_store,
)
from backend.app.persistence.database import Database
from backend.app.schemas.ingestion import (
    HeartbeatPayload,
    IngestResponse,
    StateChangePayload,
)
from backend.app.state import DeviceUpdateInput, HotStateStore
from backend.app.websocket.dashboard import DashboardWebSocketManager

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["ingest"])


@router.post("/ingest", response_model=IngestResponse)
async def ingest_payload(
    payload: HeartbeatPayload | StateChangePayload,
    hot_store: HotStateStore = Depends(get_hot_store),
    database: Database = Depends(get_database),
    alert_engine: AlertEngine = Depends(get_alert_engine),
    dashboard_ws: DashboardWebSocketManager = Depends(get_dashboard_ws),
) -> IngestResponse:
    """Ingest simulator payloads and update hot/cold state."""

    server_time = datetime.now(UTC)
    if payload.message_type == "heartbeat":
        raw_changes = payload.devices
    else:
        raw_changes = payload.changes

    changes = [
        DeviceUpdateInput(
            device_id=item.device_id,
            room=item.room,
            device_type=item.device_type,
            status=item.status,
            power_draw_w=item.power_draw_w,
        )
        for item in raw_changes
    ]

    try:
        updated = hot_store.apply_updates(changes, server_time)
    except KeyError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    for record in updated:
        database.log_transition(record, server_time)

    await alert_engine.evaluate_on_ingest(updated, server_time)
    await dashboard_ws.broadcast_diff(updated, hot_store.totals(), server_time)

    logger.info(
        "Ingested %s from %s: %s updates",
        payload.message_type,
        payload.source_id,
        len(updated),
    )
    return IngestResponse(
        accepted=len(raw_changes),
        updated=[record.device_id for record in updated],
    )
