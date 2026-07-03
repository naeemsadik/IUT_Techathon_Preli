"""General conversational command."""

import logging

from discord.ext import commands

from bot.commands.formatting import format_status, format_usage
from bot.services.api_client import ApiClient, ApiClientError
from bot.services.llm_client import LlmClient, LlmClientError

logger = logging.getLogger(__name__)


def register_ask_command(
    bot: commands.Bot,
    api_client: ApiClient,
    llm_client: LlmClient,
) -> None:
    """Register the !ask command for friendly Q&A."""

    @bot.command(name="ask")
    async def ask_command(ctx: commands.Context, *, question: str) -> None:
        try:
            status = await api_client.get_status()
            usage = await api_client.get_usage()
            context = "\n\n".join([format_status(status), format_usage(usage)])
            if not llm_client.is_enabled:
                await ctx.send(
                    "LLM replies are not configured yet. Try !status, !room, or !usage."
                )
                return
            await ctx.send(await llm_client.conversation_reply(question, context))
        except ApiClientError as exc:
            logger.warning("Ask command API fetch failed: %s", exc)
            await ctx.send(f"Unable to fetch office context: {exc}")
        except LlmClientError as exc:
            logger.warning("Ask command LLM failed: %s", exc)
            await ctx.send("I could not reach the LLM right now. Try !status or !usage.")
