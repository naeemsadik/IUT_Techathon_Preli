"""Backend-only ingestion payload schemas."""

from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, Field


class DeviceUpdate(BaseModel):
    """A single device state update from the simulator."""

    device_id: str = Field(..., min_length=1)
    room: str = Field(..., min_length=1)
    device_type: str = Field(..., min_length=1)
    status: Literal["on", "off"]
    power_draw_w: int = Field(..., ge=0)


class HeartbeatPayload(BaseModel):
    """Full room state sync payload."""

    message_type: Literal["heartbeat"]
    source_id: str = Field(..., min_length=1)
    sequence: int = Field(..., ge=0)
    device_timestamp: datetime
    devices: list[DeviceUpdate] = Field(..., min_length=1)


class StateChangePayload(BaseModel):
    """Targeted diff payload."""

    message_type: Literal["state_change"]
    source_id: str = Field(..., min_length=1)
    sequence: int = Field(..., ge=0)
    device_timestamp: datetime
    changes: list[DeviceUpdate] = Field(..., min_length=1)


IngestionPayload = Annotated[
    HeartbeatPayload | StateChangePayload,
    Field(discriminator="message_type"),
]


class IngestResponse(BaseModel):
    """Response returned by the ingestion gateway."""

    accepted: int
    updated: list[str]
