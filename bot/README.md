Purpose: Discord bot client for the Phase 1 API.

Responsibilities:
- Register prefix commands.
- Fetch REST data through `ApiClient`.
- Humanize command and alert responses through Groq when configured.
- Listen to mock alert WebSocket events and post them to Discord.

Future extension:
- Add richer Discord embeds or more conversational commands without changing the backend API contract.
