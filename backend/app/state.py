"""In-memory hot state for device status and power draw."""

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from shared.models import Device, DeviceState, OfficeStatus, Room

ROOM_SLUGS: dict[str, str] = {
    "drawing_room": "Drawing Room",
    "work_room_1": "Work Room 1",
    "work_room_2": "Work Room 2",
}

ROOM_DISPLAY_TO_SLUG: dict[str, str] = {
    display.casefold(): slug for slug, display in ROOM_SLUGS.items()
}


def _build_device_manifest() -> list[dict[str, str]]:
    """Return the canonical 15-device manifest (2 fans + 3 lights per room)."""

    manifest: list[dict[str, str]] = []
    for room_slug in ROOM_SLUGS:
        for fan_index in (1, 2):
            manifest.append(
                {
                    "device_id": f"{room_slug}_fan_{fan_index}",
                    "room": room_slug,
                    "device_type": "fan",
                }
            )
        for light_index in (1, 2, 3):
            manifest.append(
                {
                    "device_id": f"{room_slug}_light_{light_index}",
                    "room": room_slug,
                    "device_type": "light",
                }
            )
    return manifest


DEVICE_MANIFEST = _build_device_manifest()


@dataclass
class DeviceRecord:
    """Runtime device state stored in hot memory."""

    device_id: str
    room: str
    device_type: str
    status: str
    power_draw_w: int
    last_changed: datetime


@dataclass
class DeviceUpdateInput:
    """Normalized device update from ingestion payloads."""

    device_id: str
    room: str
    device_type: str
    status: str
    power_draw_w: int


def effective_wattage(record: DeviceRecord) -> int:
    """Return instantaneous draw based on device status."""

    return record.power_draw_w if record.status == "on" else 0


def device_display_name(record: DeviceRecord) -> str:
    """Map device_id to a human-readable name for API responses."""

    suffix = record.device_id.rsplit("_", 1)[-1]
    type_label = record.device_type.capitalize()
    return f"{type_label} {suffix}"


def normalize_room_name(room_name: str) -> str | None:
    """Resolve a display name or slug to a room slug."""

    normalized = room_name.casefold().replace(" ", "_")
    if normalized in ROOM_SLUGS:
        return normalized
    return ROOM_DISPLAY_TO_SLUG.get(room_name.casefold())


class HotStateStore:
    """In-memory store keyed by device_id."""

    def __init__(self, startup_time: datetime | None = None) -> None:
        now = startup_time or datetime.now(UTC)
        self._devices: dict[str, DeviceRecord] = {}
        for entry in DEVICE_MANIFEST:
            self._devices[entry["device_id"]] = DeviceRecord(
                device_id=entry["device_id"],
                room=entry["room"],
                device_type=entry["device_type"],
                status="off",
                power_draw_w=0,
                last_changed=now,
            )

    def get_device(self, device_id: str) -> DeviceRecord | None:
        """Return a device record by id."""

        return self._devices.get(device_id)

    def all_devices(self) -> list[DeviceRecord]:
        """Return all device records."""

        return list(self._devices.values())

    def devices_in_room(self, room_slug: str) -> list[DeviceRecord]:
        """Return devices belonging to a room slug."""

        return [device for device in self._devices.values() if device.room == room_slug]

    def apply_updates(
        self,
        changes: list[DeviceUpdateInput],
        server_time: datetime,
    ) -> list[DeviceRecord]:
        """Apply ingestion updates and return records that actually changed."""

        updated: list[DeviceRecord] = []
        for change in changes:
            if change.device_id not in self._devices:
                raise KeyError(f"Unknown device_id: {change.device_id}")

            current = self._devices[change.device_id]
            if (
                current.status == change.status
                and current.power_draw_w == change.power_draw_w
                and current.room == change.room
                and current.device_type == change.device_type
            ):
                continue

            record = DeviceRecord(
                device_id=change.device_id,
                room=change.room,
                device_type=change.device_type,
                status=change.status,
                power_draw_w=change.power_draw_w,
                last_changed=server_time,
            )
            self._devices[change.device_id] = record
            updated.append(record)
        return updated

    def totals(self) -> dict[str, Any]:
        """Return office and per-room wattage totals."""

        room_wattage = {slug: 0 for slug in ROOM_SLUGS}
        for device in self._devices.values():
            room_wattage[device.room] += effective_wattage(device)
        return {
            "total_wattage": sum(room_wattage.values()),
            "room_wattage": room_wattage,
        }

    def get_office_status(self) -> OfficeStatus:
        """Build the shared OfficeStatus model from hot state."""

        rooms: list[Room] = []
        for room_slug, display_name in ROOM_SLUGS.items():
            devices = self.devices_in_room(room_slug)
            api_devices = [
                Device(
                    name=device_display_name(device),
                    state=DeviceState.ON if device.status == "on" else DeviceState.OFF,
                    wattage=effective_wattage(device),
                )
                for device in sorted(devices, key=lambda item: item.device_id)
            ]
            total = sum(device.wattage for device in api_devices)
            rooms.append(
                Room(name=display_name, devices=api_devices, total_wattage=total)
            )

        return OfficeStatus(
            office_status="operational",
            total_wattage=sum(room.total_wattage for room in rooms),
            rooms=rooms,
        )

    def get_room(self, room_name: str) -> Room | None:
        """Return a single room by display name or slug."""

        room_slug = normalize_room_name(room_name)
        if room_slug is None:
            return None

        status = self.get_office_status()
        display_name = ROOM_SLUGS[room_slug]
        return next((room for room in status.rooms if room.name == display_name), None)
