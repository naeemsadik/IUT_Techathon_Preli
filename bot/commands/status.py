"""Status command."""

import logging

from discord.ext import commands

from bot.commands.formatting import format_status
from bot.services.api_client import ApiClient, ApiClientError

logger = logging.getLogger(__name__)


def register_status_command(bot: commands.Bot, api_client: ApiClient) -> None:
    """Register the !status command."""

    @bot.command(name="status")
    async def status_command(ctx: commands.Context) -> None:
        try:
            await ctx.send(format_status(await api_client.get_status()))
        except ApiClientError as exc:
            logger.warning("Status command failed: %s", exc)
            await ctx.send(f"Unable to fetch office status: {exc}")
