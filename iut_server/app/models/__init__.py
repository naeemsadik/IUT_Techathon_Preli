"""Backend model aliases backed by shared contracts."""

from shared.models import Alert, APIResponse, Device, DeviceState, OfficeStatus, Room, RoomUsage, Usage

__all__ = [
    "APIResponse",
    "Alert",
    "Device",
    "DeviceState",
    "OfficeStatus",
    "Room",
    "RoomUsage",
    "Usage",
]
