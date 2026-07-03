"""Office status model."""

from pydantic import BaseModel, Field

from shared.models.room import Room


class OfficeStatus(BaseModel):
    """Current office-wide energy state."""

    office_status: str = Field(..., min_length=1)
    total_wattage: int = Field(..., ge=0)
    rooms: list[Room]
