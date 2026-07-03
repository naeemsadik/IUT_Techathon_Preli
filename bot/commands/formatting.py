"""Message formatting helpers for Discord commands."""

from shared.models import OfficeStatus, Room, Usage


def format_room(room: Room) -> str:
    """Format one room for Discord."""

    lines = [f"**{room.name}**", f"Power: {room.total_wattage}W"]
    lines.extend(f"{device.name} {device.state.value}" for device in room.devices)
    return "\n".join(lines)


def format_status(status: OfficeStatus) -> str:
    """Format office status for Discord."""

    sections = [
        "**Office Status**",
        f"Total Power: {status.total_wattage}W",
        "",
    ]
    sections.extend(format_room(room) for room in status.rooms)
    return "\n\n".join(sections)


def format_usage(usage: Usage) -> str:
    """Format usage summary for Discord."""

    lines = [
        "**Energy Usage**",
        f"Daily: {usage.daily_kwh:.1f} kWh",
        f"Weekly: {usage.weekly_kwh:.1f} kWh",
        f"Monthly: {usage.monthly_kwh:.1f} kWh",
        "",
        "**Per Room**",
    ]
    lines.extend(f"{room.room_name}: {room.kwh:.1f} kWh" for room in usage.per_room)
    return "\n".join(lines)
