"""Static repository implementation for Phase 1."""

from shared.models import Device, DeviceState, OfficeStatus, Room, RoomUsage, Usage


class MockBotRepository:
    """Mock repository with deterministic office data."""

    def __init__(self) -> None:
        self._rooms = [
            Room(
                name="Drawing Room",
                devices=[
                    Device(name="Fan", state=DeviceState.ON, wattage=75),
                    Device(name="Light", state=DeviceState.OFF, wattage=0),
                    Device(name="AC", state=DeviceState.ON, wattage=1200),
                ],
                total_wattage=1275,
            ),
            Room(
                name="Work Room 1",
                devices=[
                    Device(name="Fan", state=DeviceState.ON, wattage=75),
                    Device(name="Light", state=DeviceState.ON, wattage=40),
                ],
                total_wattage=115,
            ),
            Room(
                name="Work Room 2",
                devices=[
                    Device(name="Fan", state=DeviceState.OFF, wattage=0),
                    Device(name="Light", state=DeviceState.ON, wattage=40),
                ],
                total_wattage=40,
            ),
        ]

    async def get_status(self) -> OfficeStatus:
        """Return current office status."""

        total_wattage = sum(room.total_wattage for room in self._rooms)
        return OfficeStatus(
            office_status="operational",
            total_wattage=total_wattage,
            rooms=self._rooms,
        )

    async def get_room(self, room_name: str) -> Room | None:
        """Return a room matched by case-insensitive name."""

        normalized = room_name.casefold()
        return next(
            (room for room in self._rooms if room.name.casefold() == normalized),
            None,
        )

    async def get_usage(self) -> Usage:
        """Return static usage values."""

        return Usage(
            daily_kwh=18.4,
            weekly_kwh=126.7,
            monthly_kwh=534.2,
            per_room=[
                RoomUsage(room_name="Drawing Room", kwh=10.8),
                RoomUsage(room_name="Work Room 1", kwh=4.6),
                RoomUsage(room_name="Work Room 2", kwh=3.0),
            ],
        )
