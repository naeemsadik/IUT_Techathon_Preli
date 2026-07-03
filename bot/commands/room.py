"""Room command."""

import logging

from discord.ext import commands

from bot.commands.formatting import format_room
from bot.services.api_client import ApiClient, ApiClientError, ApiNotFoundError

logger = logging.getLogger(__name__)


def register_room_command(bot: commands.Bot, api_client: ApiClient) -> None:
    """Register the !room command."""

    @bot.command(name="room")
    async def room_command(ctx: commands.Context, *, room_name: str) -> None:
        try:
            await ctx.send(format_room(await api_client.get_room(room_name)))
        except ApiNotFoundError:
            await ctx.send(f"Unknown room: {room_name}")
        except ApiClientError as exc:
            logger.warning("Room command failed: %s", exc)
            await ctx.send(f"Unable to fetch room status: {exc}")
