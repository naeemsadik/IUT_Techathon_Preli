"""Common API response models."""

from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    """Standard envelope for API responses."""

    success: bool = True
    data: T
    message: str | None = None


class ErrorResponse(BaseModel):
    """Standard error response body."""

    detail: str = Field(..., min_length=1)
