"""Discord bot entry point."""

import asyncio
import logging

import discord
import websockets
from discord.ext import commands
from pydantic import ValidationError

from bot.commands import register_commands
from bot.config import get_settings
from bot.services.api_client import ApiClient
from bot.services.llm_client import LlmClient, LlmClientError
from shared.models import Alert

logger = logging.getLogger(__name__)
RECONNECT_DELAY_SECONDS = 5


def build_alert_ws_url(api_base_url: str) -> str:
    """Build the alert WebSocket URL from the configured REST base URL."""

    if api_base_url.startswith("https://"):
        return f"wss://{api_base_url.removeprefix('https://').rstrip('/')}/ws/alerts"
    return f"ws://{api_base_url.removeprefix('http://').rstrip('/')}/ws/alerts"


async def listen_for_alerts(
    bot: commands.Bot,
    channel_id: int,
    api_base_url: str,
    llm_client: LlmClient,
) -> None:
    """Listen to alert WebSocket events and post them to Discord."""

    ws_url = build_alert_ws_url(api_base_url)
    while not bot.is_closed():
        try:
            logger.info("WebSocket connected attempt: %s", ws_url)
            async with websockets.connect(ws_url) as websocket:
                logger.info("WebSocket connected: %s", ws_url)
                async for message in websocket:
                    try:
                        alert = Alert.model_validate_json(message)
                    except ValidationError:
                        logger.warning("Malformed alert received: %s", message)
                        continue

                    logger.info("Alert received: %s", alert.message)
                    channel = bot.get_channel(channel_id) or await bot.fetch_channel(channel_id)
                    if hasattr(channel, "send"):
                        try:
                            message = await llm_client.alert_reply(alert.message)
                        except LlmClientError:
                            message = f"Alert: {alert.message}"
                        await channel.send(message)
        except (discord.DiscordException, OSError, websockets.WebSocketException) as exc:
            logger.warning("Alert listener disconnected: %s", exc)
            logger.info("Reconnect attempt in %s seconds", RECONNECT_DELAY_SECONDS)
            await asyncio.sleep(RECONNECT_DELAY_SECONDS)


def create_bot() -> commands.Bot:
    """Create and configure the Discord bot."""

    settings = get_settings()
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s - %(message)s",
    )

    intents = discord.Intents.default()
    intents.message_content = True
    discord_bot = commands.Bot(command_prefix=settings.command_prefix, intents=intents)
    api_client = ApiClient(settings.api_base_url)
    llm_client = LlmClient(
        api_key=settings.groq_api_key,
        model=settings.groq_model,
        enabled=settings.llm_enabled,
    )
    register_commands(discord_bot, api_client, llm_client)

    @discord_bot.event
    async def on_ready() -> None:
        logger.info("Bot connected as %s", discord_bot.user)
        if settings.alert_channel_id is not None:
            discord_bot.loop.create_task(
                listen_for_alerts(
                    bot=discord_bot,
                    channel_id=settings.alert_channel_id,
                    api_base_url=settings.api_base_url,
                    llm_client=llm_client,
                )
            )
        else:
            logger.warning("ALERT_CHANNEL_ID is not configured; alert listener disabled")

    @discord_bot.event
    async def on_command_error(ctx: commands.Context, error: commands.CommandError) -> None:
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("Please include the required command argument.")
            return
        logger.exception("Unhandled command error: %s", error)
        await ctx.send("Sorry, that command failed.")

    async def close() -> None:
        await api_client.close()
        await llm_client.close()
        await commands.Bot.close(discord_bot)

    discord_bot.close = close  # type: ignore[method-assign]
    return discord_bot


def main() -> None:
    """Run the Discord bot."""

    settings = get_settings()
    if not settings.discord_token:
        raise RuntimeError("DISCORD_TOKEN is required to start the bot.")
    create_bot().run(settings.discord_token)


if __name__ == "__main__":
    main()
