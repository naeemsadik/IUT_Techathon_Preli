"""Energy usage models."""

from pydantic import BaseModel, Field


class RoomUsage(BaseModel):
    """Energy usage for one room."""

    room_name: str = Field(..., min_length=1)
    kwh: float = Field(..., ge=0)


class Usage(BaseModel):
    """Aggregate usage summary."""

    daily_kwh: float = Field(..., ge=0)
    weekly_kwh: float = Field(..., ge=0)
    monthly_kwh: float = Field(..., ge=0)
    per_room: list[RoomUsage]
