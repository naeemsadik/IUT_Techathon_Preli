"""Room command."""

import logging

from discord.ext import commands

from bot.commands.formatting import format_room
from bot.services.api_client import ApiClient, ApiClientError, ApiNotFoundError
from bot.services.llm_client import LlmClient, LlmClientError

logger = logging.getLogger(__name__)


def register_room_command(
    bot: commands.Bot,
    api_client: ApiClient,
    llm_client: LlmClient,
) -> None:
    """Register the !room command."""

    @bot.command(name="room")
    async def room_command(ctx: commands.Context, *, room_name: str) -> None:
        try:
            deterministic = format_room(await api_client.get_room(room_name))
            try:
                await ctx.send(await llm_client.command_reply("room", deterministic))
            except LlmClientError:
                await ctx.send(deterministic)
        except ApiNotFoundError:
            await ctx.send(f"Unknown room: {room_name}")
        except ApiClientError as exc:
            logger.warning("Room command failed: %s", exc)
            await ctx.send(f"Unable to fetch room status: {exc}")
