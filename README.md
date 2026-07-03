# Office Energy Monitoring System - Bot Phase

This repository currently implements Phase 1 only: a mock FastAPI server, a Discord bot, shared Pydantic models, a mock alert WebSocket stream, documentation, and tests.

The simulator, dashboard, database, Redis, real alert engine, power calculations, device ingestion, and LLM integration are intentionally out of scope for this phase.

## Architecture

- `shared/` defines the API contract once with Pydantic v2 models.
- `backend/` exposes bot-facing REST endpoints and `/ws/alerts`.
- `backend/app/repositories/` hides mock data behind `BotRepository`.
- `backend/app/services/` contains the service layer used by routes.
- `bot/` contains Discord prefix commands, the reusable `ApiClient`, and the alert listener.

The intended future swap is:

```text
MockBotRepository -> RealBotRepository
```

Routes and Discord commands should not need to change when that happens.

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Copy the example environment files before running services:

```bash
copy backend\.env.example backend\.env
copy bot\.env.example bot\.env
```

## Run Backend

From the repository root:

```bash
uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```

Available endpoints:

- `GET /api/status`
- `GET /api/room/{room_name}`
- `GET /api/usage`
- `GET /api/health`
- `WS /ws/alerts`

## Run Bot

Set `DISCORD_TOKEN`, `API_BASE_URL`, `ALERT_CHANNEL_ID`, and `COMMAND_PREFIX` in `bot/.env`, then run:

```bash
python -m bot.bot
```

Commands:

- `!status`
- `!room Drawing Room`
- `!usage`

The bot also connects to `/ws/alerts` and posts fake alerts to the configured Discord channel.

## Testing

```bash
pytest
```

Tests cover the mock repository, service layer, FastAPI routes with dependency overrides, command formatting, and the mock API client transport.

## Future Phases

Planned additions include simulator ingestion, SQLite, Redis, dashboard WebSockets, a real alert engine, usage calculations, and LLM-assisted Discord responses.
