Purpose: shared contracts used by both the FastAPI backend and Discord bot.

Responsibilities:
- Define Pydantic models for API responses, rooms, devices, usage, and alerts.
- Keep the public API contract in one place so clients do not duplicate schemas.

Future extension:
- Add new fields here when simulator, persistence, dashboard, or alert-engine phases expand the API.
