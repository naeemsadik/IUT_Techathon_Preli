"""Usage command."""

import logging

from discord.ext import commands

from bot.commands.formatting import format_usage
from bot.services.api_client import ApiClient, ApiClientError

logger = logging.getLogger(__name__)


def register_usage_command(bot: commands.Bot, api_client: ApiClient) -> None:
    """Register the !usage command."""

    @bot.command(name="usage")
    async def usage_command(ctx: commands.Context) -> None:
        try:
            await ctx.send(format_usage(await api_client.get_usage()))
        except ApiClientError as exc:
            logger.warning("Usage command failed: %s", exc)
            await ctx.send(f"Unable to fetch usage: {exc}")
