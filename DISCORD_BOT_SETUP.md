# Discord Bot Setup and Testing Guide

This guide explains how to configure and test the Discord bot with the FastAPI backend and Groq LLM replies.

## 1. Install Dependencies

From the repository root:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## 2. Create a Discord Bot

1. Go to the Discord Developer Portal: https://discord.com/developers/applications
2. Create a new application.
3. Open the application and go to **Bot**.
4. Create a bot user.
5. Copy the bot token.
6. Enable **Message Content Intent** under privileged gateway intents.

## 3. Invite the Bot to Your Server

In the Developer Portal:

1. Go to **OAuth2** -> **URL Generator**.
2. Select scopes:
   - `bot`
3. Select bot permissions:
   - `Send Messages`
   - `Read Message History`
   - `View Channels`
4. Open the generated URL and invite the bot to your Discord server.

## 4. Get the Alert Channel ID

In Discord:

1. Open **User Settings** -> **Advanced**.
2. Enable **Developer Mode**.
3. Right-click the channel where alerts should be posted.
4. Click **Copy Channel ID**.

## 5. Configure Environment Variables

Create `bot/.env` from the example:

```bash
copy bot\.env.example bot\.env
```

Edit `bot/.env`:

```env
DISCORD_TOKEN=your-discord-bot-token
API_BASE_URL=http://127.0.0.1:8000
ALERT_CHANNEL_ID=your-discord-channel-id
COMMAND_PREFIX=!
GROQ_API_KEY=your-groq-api-key
GROQ_MODEL=llama-3.3-70b-versatile
LLM_ENABLED=true
```

Do not commit `bot/.env`. Keep real API keys only in local environment files.

## 6. Start the Backend

In one terminal:

```bash
.venv\Scripts\activate
uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```

Check that the backend works:

```bash
curl http://127.0.0.1:8000/api/health
curl http://127.0.0.1:8000/api/status
curl http://127.0.0.1:8000/api/usage
```

## 7. Start the Discord Bot

In another terminal:

```bash
.venv\Scripts\activate
python -m bot.bot
```

If setup is correct, the terminal should log that the bot connected.

## 8. Test Commands in Discord

In your Discord server, try:

```text
!status
!room Drawing Room
!room Work Room 1
!usage
!ask Why is the office power usage high?
```

Expected behavior:

- `!status` returns a friendly summary of current office status.
- `!room Drawing Room` returns a friendly room-specific summary.
- `!usage` returns a friendly usage summary.
- `!ask ...` answers conversationally using current mock status and usage data.

If Groq is unavailable or `LLM_ENABLED=false`, the bot falls back to deterministic formatted responses.

## 9. Test Alert Posting

Keep both backend and bot running.

The backend sends a fake alert through `/ws/alerts` every 15 seconds.

Expected behavior:

- The bot receives the alert.
- The alert is rewritten through Groq when configured.
- The bot posts the friendly alert into `ALERT_CHANNEL_ID`.

Example alerts:

```text
Drawing Room lights are still ON.
Work Room 1 exceeds usage threshold.
After-hours usage detected.
```

## 10. Run Automated Tests

From the repository root:

```bash
pytest
```

Current test coverage includes:

- Mock repository
- Service layer
- FastAPI routes
- WebSocket alert route
- Bot response formatting
- REST API client
- Groq LLM client

## Troubleshooting

### Bot does not respond

Check:

- `DISCORD_TOKEN` is correct.
- Message Content Intent is enabled in the Discord Developer Portal.
- The bot has permission to read and send messages in the channel.
- You are using the configured prefix, default `!`.

### Alerts do not appear

Check:

- `ALERT_CHANNEL_ID` is correct.
- The backend is running at `API_BASE_URL`.
- The bot has permission to send messages in that channel.

### LLM replies do not work

Check:

- `GROQ_API_KEY` is set in `bot/.env`.
- `LLM_ENABLED=true`.
- `GROQ_MODEL` is valid.
- The Groq API key has not expired or been revoked.

### Backend connection fails

Check:

- Backend is running with uvicorn.
- `API_BASE_URL=http://127.0.0.1:8000`.
- `/api/health` returns a JSON response.
