"""Room and device models."""

from enum import StrEnum

from pydantic import BaseModel, Field


class DeviceState(StrEnum):
    """Supported device states."""

    ON = "ON"
    OFF = "OFF"


class Device(BaseModel):
    """A controllable electrical device."""

    name: str = Field(..., min_length=1)
    state: DeviceState
    wattage: int = Field(..., ge=0)


class Room(BaseModel):
    """A room containing devices and aggregate power information."""

    name: str = Field(..., min_length=1)
    devices: list[Device]
    total_wattage: int = Field(..., ge=0)
