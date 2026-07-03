# Phase 1 Architecture

This phase implements only the Discord bot-facing foundation from the larger Office Energy Monitoring System architecture.

## Components

```text
Discord Bot
  | commands: !status, !room, !usage, !ask
  v
ApiClient
  | REST
  v
FastAPI routes
  v
BotService
  v
BotRepository interface
  v
MockBotRepository

FastAPI /ws/alerts
  | mock alert events
  v
Discord Bot alert listener
  v
Groq LLM client
  v
Friendly Discord message
```

## Boundaries

- Routes only handle HTTP concerns.
- Services coordinate repository calls and future business logic.
- Repositories provide data access and are replaceable.
- Discord commands format data and never contain HTTP code.
- Discord commands pass deterministic responses through the LLM client when configured.
- Shared models define the API contract for both backend and bot.

## Future Replacement Path

The mock repository can later be replaced by a SQL, Redis, or simulator-backed implementation that satisfies the same `BotRepository` protocol. The public REST contract and Discord command code should remain stable.

The full upstream architecture reference remains in `doc/ARCHITECTURE.md`.
