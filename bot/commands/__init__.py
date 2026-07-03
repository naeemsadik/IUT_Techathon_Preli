"""Discord command registration."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from discord.ext import commands

    from bot.services.api_client import ApiClient
    from bot.services.llm_client import LlmClient


def register_commands(
    bot: "commands.Bot",
    api_client: "ApiClient",
    llm_client: "LlmClient",
) -> None:
    """Register all prefix commands."""

    from bot.commands.chat import register_ask_command
    from bot.commands.room import register_room_command
    from bot.commands.status import register_status_command
    from bot.commands.usage import register_usage_command

    register_status_command(bot, api_client, llm_client)
    register_room_command(bot, api_client, llm_client)
    register_usage_command(bot, api_client, llm_client)
    register_ask_command(bot, api_client, llm_client)
