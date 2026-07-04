# IUT Energy Monitor

A real-time office energy monitoring system for three rooms: Drawing Room,
Work Room 1, and Work Room 2. The system ingests device state, tracks live power
usage, stores historical transitions in SQLite, broadcasts live updates over
WebSockets, and optionally posts alerts to Discord.

Live frontend:

```text
https://iut-energy-monitor.vercel.app/
```

Current backend:

```text
https://iut-techathon-preli.onrender.com
```

API docs:

```text
https://iut-techathon-preli.onrender.com/docs
```

---

## Features

| Area | What it does |
|---|---|
| Live monitoring | Shows current device states and total wattage per room |
| Historical analytics | Stores device transitions and calculates usage from SQLite |
| Real-time updates | Pushes state changes to the frontend through `/ws/live` |
| Alerts | Detects off-hours usage, room-duration, and per-device-duration issues |
| Simulator | Generates demo device changes for all 15 devices |
| Discord bot | Optional command and alert interface |
| Deployment | Frontend on Vercel, backend on Render |

---

## Architecture

```text
Simulator / Hardware
        |
        | POST /api/ingest
        v
iut_server FastAPI backend
        |-- SQLite history
        |-- /ws/live to frontend
        |-- /ws/alerts to Discord bot
        |
        v
Next.js frontend on Vercel
```

The backend is the source of truth. The frontend reads REST endpoints for initial
state and analytics, then listens to `/ws/live` for live changes.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 14, React, TypeScript, Tailwind CSS, Recharts, Zustand |
| Backend | FastAPI, Pydantic v2, SQLite, asyncio |
| Realtime | WebSockets |
| Bot | discord.py, httpx, optional Groq LLM |
| Testing | pytest, pytest-asyncio |
| Deployment | Vercel frontend, Render backend |

---

## Project Structure

```text
IUT_Techathon_Preli/
├── iut_server/           # FastAPI backend server
│   ├── app/api/          # REST and WebSocket routes
│   ├── app/persistence/  # SQLite persistence
│   ├── app/repositories/ # Bot-facing data access
│   ├── app/services/     # Business services
│   └── app/websocket/    # WebSocket managers
├── frontend/             # Next.js frontend
├── simulator/            # Synthetic 15-device data generator
├── bot/                  # Discord bot
├── shared/               # Shared Pydantic response models
├── examples/             # Example ingest payloads
├── tests/                # Python test suite
├── doc/                  # Architecture and deployment docs
├── docker-compose.yaml   # Compose config for Docker/Coolify-style deploys
├── requirements.txt      # Python dependencies
└── runtime.txt           # Render Python version
```

---

## Live Environment

### Vercel Frontend

Add these environment variables in Vercel:

```env
NEXT_PUBLIC_API_BASE_URL=https://iut-techathon-preli.onrender.com
NEXT_PUBLIC_WS_BASE_URL=wss://iut-techathon-preli.onrender.com
```

Redeploy Vercel after changing `NEXT_PUBLIC_*` variables because they are baked
into the frontend build.

### Render Backend

Render build command:

```bash
pip install -r requirements.txt
```

Render start command:

```bash
uvicorn iut_server.app.main:app --host 0.0.0.0 --port $PORT
```

Render environment variables:

```env
HOST=0.0.0.0
PORT=8000
DEBUG=false

OFFICE_START=09:00
OFFICE_END=17:00
DURATION_THRESHOLD_SECONDS=7200
DEVICE_DURATION_THRESHOLD_SECONDS=3600
ALERT_SWEEP_INTERVAL_SECONDS=30

SQLITE_PATH=data/office_energy.db
CORS_ALLOW_ORIGINS=https://iut-energy-monitor.vercel.app,https://iut-techathon-preli.vercel.app

ENABLE_SIMULATOR=true
SIMULATOR_API_URL=https://iut-techathon-preli.onrender.com
SIMULATOR_TOGGLE_PROB=0.6
SIMULATOR_HEARTBEAT_EVERY_N=10

ENABLE_DISCORD_BOT=false
API_BASE_URL=https://iut-techathon-preli.onrender.com
COMMAND_PREFIX=!
LLM_ENABLED=false
GROQ_MODEL=llama-3.3-70b-versatile
```

Do not set blank optional variables such as `SIMULATOR_SEED=` on Render. Omit
them unless you need them.

For persistent SQLite on a paid Render service, mount a disk at:

```text
/var/data
```

Then set:

```env
SQLITE_PATH=/var/data/office_energy.db
```

---

## Local Development

### Backend

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy iut_server\.env.example iut_server\.env
uvicorn iut_server.app.main:app --host 127.0.0.1 --port 8000 --reload
```

Backend docs:

```text
http://127.0.0.1:8000/docs
```

### Frontend

```powershell
cd frontend
npm install
npm run dev
```

Frontend dev URL:

```text
http://localhost:3000
```

### Simulator

Run against local backend:

```powershell
python -m simulator.simulator
```

Run against Render backend:

```powershell
python -m simulator.simulator --url https://iut-techathon-preli.onrender.com --probability 0.6
```

The simulator controls 15 devices total:

| Room | Devices |
|---|---|
| Drawing Room | 2 fans, 3 lights |
| Work Room 1 | 2 fans, 3 lights |
| Work Room 2 | 2 fans, 3 lights |

---

## API Reference

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/health` | Backend health check |
| `GET` | `/api/status` | Full live office status |
| `GET` | `/api/room/{room_name}` | Single room status |
| `GET` | `/api/usage` | Daily, weekly, monthly usage |
| `GET` | `/api/history?range=24h` | Time-series analytics |
| `POST` | `/api/ingest` | Ingest heartbeat or state change payload |
| `WS` | `/ws/live` | Live frontend state diffs |
| `WS` | `/ws/alerts` | Live alert stream |

Example ingest:

```powershell
curl.exe -X POST "http://127.0.0.1:8000/api/ingest" `
  -H "Content-Type: application/json" `
  --data-binary "@examples/ingest_state_change.json"
```

---

## Discord Bot

The bot can run separately with:

```powershell
python -m bot.bot
```

It can also run inside the backend process when these Render env vars are set:

```env
ENABLE_DISCORD_BOT=true
DISCORD_TOKEN=your-discord-bot-token
ALERT_CHANNEL_ID=your-alert-channel-id
API_BASE_URL=https://iut-techathon-preli.onrender.com
COMMAND_PREFIX=!
LLM_ENABLED=false
```

Commands:

| Command | Description |
|---|---|
| `!status` | Full office power summary |
| `!room Drawing Room` | Single room status |
| `!usage` | Energy usage summary |
| `!ask ...` | Optional LLM-powered question |

---

## Testing

Run all backend tests:

```powershell
python -m pytest
```

Build the frontend:

```powershell
cd frontend
npm run build
```

---

## Deployment Notes

- The frontend is deployed from `frontend/` to Vercel.
- The backend is deployed to Render as a Python web service.
- `runtime.txt` pins Python for Render.
- `ENABLE_SIMULATOR=true` starts the demo generator inside the backend server.
- `CORS_ALLOW_ORIGINS` must include the Vercel frontend domain.
- `NEXT_PUBLIC_WS_BASE_URL` must use `wss://` in production.
- SQLite data is ephemeral on free Render unless you add a persistent disk.

More details are in [doc/DEPLOYMENT.md](doc/DEPLOYMENT.md).

---

## Documentation

| Document | Description |
|---|---|
| [doc/DEPLOYMENT.md](doc/DEPLOYMENT.md) | Render, Vercel, Docker, and environment setup |
| [doc/ARCHITECTURE.md](doc/ARCHITECTURE.md) | System architecture and design decisions |
| [doc/SYSTEM_GUIDE.md](doc/SYSTEM_GUIDE.md) | End-to-end technical guide |
| [doc/SIMULATOR.md](doc/SIMULATOR.md) | Simulator behavior and implementation |
| [doc/HARDWARE.md](doc/HARDWARE.md) | ESP32 hardware reference |
| [DISCORD_BOT_SETUP.md](DISCORD_BOT_SETUP.md) | Discord bot setup |

---

## Status

The live frontend is connected to the Render backend. The backend can also run
the embedded simulator so the frontend receives ongoing fan/light updates without
a separate worker service.
