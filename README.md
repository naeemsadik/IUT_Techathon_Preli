# Office Energy Monitoring System

Monitor office energy usage across three rooms (Drawing Room, Work Room 1, Work Room 2) with a FastAPI backend, SQLite logging, real-time alerts, a Discord bot interface, a synthetic device simulator, and a Next.js frontend.

**What's working today:** ingestion API, hot/cold state, dual-path alert engine (off-hours, room-duration, per-device-duration), REST + WebSocket endpoints, Discord bot with optional Groq LLM replies, `simulator.py` data source, and the Next.js frontend in `frontend/`.

---

## Prerequisites

| Requirement | Notes |
|---|---|
| **Python 3.12+** | Check with `python --version` |
| **Git** | To clone the repository |
| **Discord account** | Only if running the Discord bot |
| **Groq API key** | Optional — bot falls back to plain text without it |

---

## Quick Start (5 minutes)

### 1. Clone and install

```powershell
git clone <repository-url>
cd IUT_Techathon_Preli

python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

On macOS/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure environment

```powershell
copy backend\.env.example backend\.env
copy bot\.env.example bot\.env      # optional — only needed for Discord bot
```

The backend runs with defaults out of the box. The bot requires a Discord token (see [Discord bot setup](#discord-bot-setup) below).

### 3. Start backend + simulator

The demo launcher starts the backend and simulator in one command.

**Windows — pure batch (no PowerShell):**

```cmd
scripts\demo.cmd            REM start backend + simulator
scripts\demo.cmd stop       REM stop everything
```

**Windows — PowerShell** (either `pwsh` for v7+ or `powershell` for v5.1):

```powershell
powershell -File scripts\demo.ps1              # start everything
powershell -File scripts\demo.ps1 -WithBot     # also start Discord bot
powershell -File scripts\demo.ps1 -Stop        # stop everything
```

**Linux / macOS:**

```bash
./scripts/demo.sh              # start everything
./scripts/demo.sh --with-bot   # also start Discord bot
./scripts/demo.sh --stop       # stop everything
```

Once it's up:

- **Backend API docs** → <http://127.0.0.1:8000/docs>

Start the frontend from `frontend/`:

```powershell
cd frontend
npm install
npm run dev
```

- **Frontend** → <http://localhost:3000>

Or run the components manually in separate terminals — see [Running Everything Together](#running-everything-together) below.

### 4. Run tests

```powershell
pytest
```

---

## Project Structure

```text
IUT_Techathon_Preli/
├── backend/app/          # FastAPI server (ingestion, state, alerts, SQLite)
├── bot/                  # Discord bot
├── shared/models/        # Pydantic API contracts
├── simulator/            # 15-device synthetic data source (Phase 3)
├── frontend/             # Next.js frontend
├── scripts/              # One-command demo launchers
├── examples/             # Sample ingest JSON files
├── tests/                # pytest suite
└── doc/                  # Architecture and guides
    ├── ARCHITECTURE.md   # System design
    ├── SYSTEM_GUIDE.md   # How it works + detailed testing
    ├── SIMULATOR.md      # Simulator internals
    ├── HIGH_LEVEL_DIAGRAMS.md  # Phase 3 system diagrams
    ├── HARDWARE.md       # Reference ESP32 schematic
    └── DEMO.md           # Live demo walk-through
```

---

## Running the Backend

From the repository root with the virtual environment activated:

```powershell
uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```

### API Endpoints

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/ingest` | Ingest device state (heartbeat or state_change) |
| `GET` | `/api/status` | Full office status and wattage |
| `GET` | `/api/room/{room_name}` | Single room (`Drawing Room` or `drawing_room`) |
| `GET` | `/api/usage` | Daily / weekly / monthly kWh |
| `GET` | `/api/health` | Server health check |
| `WS` | `/ws/alerts` | Real-time alert stream |
| `WS` | `/ws/live` | Hot-state diffs for the Next.js frontend |

Interactive docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

### Backend Environment Variables

Edit `backend/.env` (copy from `backend/.env.example`):

| Variable | Default | Description |
|---|---|---|
| `HOST` | `127.0.0.1` | Bind host |
| `PORT` | `8000` | Bind port |
| `DEBUG` | `false` | Enable debug logging |
| `OFFICE_START` | `09:00` | Office hours start (24h, HH:MM) |
| `OFFICE_END` | `17:00` | Office hours end |
| `DURATION_THRESHOLD_SECONDS` | `7200` | Room all-ON alert threshold (use `20` for demos) |
| `DEVICE_DURATION_THRESHOLD_SECONDS` | `3600` | Per-device ON alert threshold (use `0` to fire on every ingest) |
| `ALERT_SWEEP_INTERVAL_SECONDS` | `30` | Background alert sweep interval |
| `SQLITE_PATH` | `data/office_energy.db` | SQLite database file |

SQLite data is created automatically on first startup.

---

## Feeding Data to the Backend

Until `simulator.py` lands (Phase 3), use manual API calls or the example JSON files.

### Option A — JSON file (recommended on Windows)

```powershell
# Turn on a fan
curl.exe -X POST "http://127.0.0.1:8000/api/ingest" `
  -H "Content-Type: application/json" `
  --data-binary "@examples/ingest_state_change.json"

# Sync a full room (Drawing Room heartbeat)
curl.exe -X POST "http://127.0.0.1:8000/api/ingest" `
  -H "Content-Type: application/json" `
  --data-binary "@examples/ingest_heartbeat.json"
```

### Option B — PowerShell native

```powershell
$body = @{
  message_type     = "state_change"
  source_id        = "esp32-work-room-1"
  sequence         = 1
  device_timestamp = "2026-07-04T14:00:30Z"
  changes          = @(
    @{
      device_id    = "work_room_1_fan_1"
      room         = "work_room_1"
      device_type  = "fan"
      status       = "on"
      power_draw_w = 60
    }
  )
} | ConvertTo-Json -Depth 5

Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/ingest" -Method POST `
  -ContentType "application/json" -Body $body
```

### Option C — Phase 3 simulator

```powershell
python -m simulator.simulator
```

The simulator drives 15 devices (2 fans + 3 lights × 3 rooms), staggered at
3s / 5s / 7s intervals. Tunable via env vars (`SIMULATOR_TOGGLE_PROB`,
`SIMULATOR_HEARTBEAT_EVERY_N`, `SIMULATOR_SEED`) and CLI flags (`--url`,
`--probability`, `--room`, `--seed`).

See [doc/SIMULATOR.md](doc/SIMULATOR.md) for the implementation guide.

> **PowerShell tip:** `curl` is an alias for `Invoke-WebRequest`. Use `curl.exe` for real curl, or `Invoke-RestMethod` for native HTTP. Avoid escaped `\"` inside double-quoted strings — use single quotes or a JSON file instead.

---

## Discord Bot Setup

### 1. Create a Discord bot

1. Open the [Discord Developer Portal](https://discord.com/developers/applications).
2. Create a new application → **Bot** → copy the token.
3. Enable **Message Content Intent** under Privileged Gateway Intents.
4. Invite the bot to your server (OAuth2 → URL Generator → `bot` scope → Send Messages permission).

### 2. Get the alert channel ID

1. Enable **Developer Mode** in Discord (Settings → Advanced).
2. Right-click the target channel → **Copy Channel ID**.

### 3. Configure `bot/.env`

```env
DISCORD_TOKEN=your-discord-bot-token
API_BASE_URL=http://127.0.0.1:8000
ALERT_CHANNEL_ID=your-discord-channel-id
COMMAND_PREFIX=!
GROQ_API_KEY=your-groq-api-key
GROQ_MODEL=llama-3.3-70b-versatile
LLM_ENABLED=true
```

Set `LLM_ENABLED=false` or leave `GROQ_API_KEY` empty to skip LLM rewriting.

Full walkthrough: [DISCORD_BOT_SETUP.md](DISCORD_BOT_SETUP.md)

### 4. Start the bot

Backend must be running first.

```powershell
python -m bot.bot
```

### Discord Commands

| Command | Description |
|---|---|
| `!status` | Full office power summary |
| `!room Drawing Room` | Single room status |
| `!usage` | Energy usage (kWh) |
| `!ask Why is power high?` | Free-form question via LLM |

The bot also listens on `/ws/alerts` and posts real alerts to the configured channel.

---

## Running Everything Together

Open separate terminals (or use `scripts/demo.ps1` for backend + simulator):

| Terminal | Command | URL / Output |
|---|---|---|
| 1 — Backend | `uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload` | <http://127.0.0.1:8000> |
| 2 — Simulator | `python -m simulator.simulator` | POSTs to `/api/ingest` |
| 3 — Frontend | `cd frontend && npm run dev` | <http://localhost:3000> |
| 4 — Discord bot (optional) | `python -m bot.bot` | Listens on `/ws/alerts` |

---

## Testing

### Automated tests

```powershell
pytest                  # all tests
pytest tests/test_phase2.py -v   # Phase 2 integration only
```

### Manual smoke test

| Step | Command | Expected |
|---|---|---|
| 1 | `Invoke-RestMethod .../api/health` | `{ status: "ok" }` |
| 2 | POST `examples/ingest_state_change.json` | `{ accepted: 1, updated: [...] }` |
| 3 | `Invoke-RestMethod .../api/status` | `total_wattage: 60` |
| 4 | `!status` in Discord | Matches API data |
| 5 | `pytest` | All tests pass |

### Demo alert mode

Set in `backend/.env`, then restart the backend:

```env
DURATION_THRESHOLD_SECONDS=20
```

Turn all 5 devices in one room ON via ingest and wait up to 30 seconds for a room duration alert.

Detailed test procedures: [doc/SYSTEM_GUIDE.md](doc/SYSTEM_GUIDE.md)

---

## Devices

15 devices total — 2 fans + 3 lights per room.

| Room | Slug | Example device ID |
|---|---|---|
| Drawing Room | `drawing_room` | `drawing_room_fan_1` |
| Work Room 1 | `work_room_1` | `work_room_1_light_2` |
| Work Room 2 | `work_room_2` | `work_room_2_fan_2` |

Rated wattages used in examples: **fan 60W**, **light 15W**.

---

## Troubleshooting

| Problem | Solution |
|---|---|
| `curl` JSON decode error on ingest | Use `curl.exe` with a JSON file or single-quoted `-d '...'` — see [Feeding Data](#feeding-data-to-the-backend) |
| `Invoke-WebRequest` security prompt | Use `Invoke-RestMethod` or `curl.exe` instead of `curl` |
| `/api/status` shows 0W after ingest | Confirm ingest returned `200` and check the `updated` list in the response |
| Discord bot cannot connect | Verify backend is running and `API_BASE_URL` in `bot/.env` is correct |
| No alerts in Discord | Check `ALERT_CHANNEL_ID`, confirm device is ON outside office hours or duration threshold met |
| `pytest` import errors | Run from repo root with venv activated; `pythonpath` is set in `pyproject.toml` |
| SQLite permission errors | Ensure `data/` directory is writable or change `SQLITE_PATH` in `backend/.env` |

---

## Documentation

| Document | Description |
|---|---|
| [doc/HIGH_LEVEL_DIAGRAMS.md](doc/HIGH_LEVEL_DIAGRAMS.md) | Phase 3 system diagrams — Version 1 (memory + SQLite) and Version 2 (Redis + PostgreSQL) |
| [doc/ARCHITECTURE.md](doc/ARCHITECTURE.md) | System design, components, alert rules, trade-offs |
| [doc/SYSTEM_GUIDE.md](doc/SYSTEM_GUIDE.md) | End-to-end flows, diagrams, full test guide |
| [doc/SIMULATOR.md](doc/SIMULATOR.md) | Phase 3 `simulator.py` implementation guide |
| [doc/HARDWARE.md](doc/HARDWARE.md) | ESP32 + relay reference schematic (informational) |
| [doc/DEMO.md](doc/DEMO.md) | Live demo walk-through and one-click launcher |
| [DISCORD_BOT_SETUP.md](DISCORD_BOT_SETUP.md) | Step-by-step Discord bot configuration |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Short architecture overview with link to full doc |

---

## Tech Stack

- **Backend:** FastAPI, Pydantic v2, SQLite (stdlib), asyncio
- **Bot:** discord.py, httpx, Groq API (optional)
- **Tests:** pytest, pytest-asyncio

No Redis or PostgreSQL required for local development.
