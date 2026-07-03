Purpose: FastAPI server for the Discord bot phase.

Responsibilities:
- Expose REST endpoints consumed by the bot.
- Provide a mock alert WebSocket stream.
- Keep data access behind repository interfaces and formatting behind services.

Future extension:
- Replace `MockBotRepository` with a real database-backed implementation without changing routes or bot commands.
