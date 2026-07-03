"""Alert event model."""

from datetime import datetime

from pydantic import BaseModel, Field


class Alert(BaseModel):
    """A proactive alert delivered to bot clients."""

    id: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)
    severity: str = Field(default="info", min_length=1)
    created_at: datetime
