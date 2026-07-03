"""Usage command."""

import logging

from discord.ext import commands

from bot.commands.formatting import format_usage
from bot.services.api_client import ApiClient, ApiClientError
from bot.services.llm_client import LlmClient, LlmClientError

logger = logging.getLogger(__name__)


def register_usage_command(
    bot: commands.Bot,
    api_client: ApiClient,
    llm_client: LlmClient,
) -> None:
    """Register the !usage command."""

    @bot.command(name="usage")
    async def usage_command(ctx: commands.Context) -> None:
        try:
            deterministic = format_usage(await api_client.get_usage())
            try:
                await ctx.send(await llm_client.command_reply("usage", deterministic))
            except LlmClientError:
                await ctx.send(deterministic)
        except ApiClientError as exc:
            logger.warning("Usage command failed: %s", exc)
            await ctx.send(f"Unable to fetch usage: {exc}")
