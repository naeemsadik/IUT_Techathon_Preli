"""REST endpoints consumed by the Discord bot."""

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from iut_server.app.dependencies import get_bot_service
from iut_server.app.services.bot_service import BotService, RoomNotFoundError
from shared.models import APIResponse, OfficeStatus, Room, Usage

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["bot"])


@router.get("/status", response_model=APIResponse[OfficeStatus])
async def get_status(
    service: BotService = Depends(get_bot_service),
) -> APIResponse[OfficeStatus]:
    """Return current office status."""

    logger.info("REST request: GET /api/status")
    return APIResponse(data=await service.get_status())


@router.get("/room/{room_name}", response_model=APIResponse[Room])
async def get_room(
    room_name: str,
    service: BotService = Depends(get_bot_service),
) -> APIResponse[Room]:
    """Return a single room by name."""

    logger.info("REST request: GET /api/room/%s", room_name)
    try:
        return APIResponse(data=await service.get_room(room_name))
    except RoomNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/usage", response_model=APIResponse[Usage])
async def get_usage(
    service: BotService = Depends(get_bot_service),
) -> APIResponse[Usage]:
    """Return energy usage summary."""

    logger.info("REST request: GET /api/usage")
    return APIResponse(data=await service.get_usage())


@router.get("/health", response_model=APIResponse[dict[str, Any]])
async def get_health(
    service: BotService = Depends(get_bot_service),
) -> APIResponse[dict[str, Any]]:
    """Return server health."""

    logger.info("REST request: GET /api/health")
    return APIResponse(data=service.get_health())
