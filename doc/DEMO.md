# Live Demo Guide

End-to-end demo of the office energy monitoring system. Assumes you have the
repo checked out, Python 3.11+ available, and (optionally) a Discord bot
token if you want to demo the bot path.

---

## 0. Quick Start (One Command)

### Windows — pure batch (no PowerShell needed)

```cmd
scripts\demo.cmd            REM backend + simulator
scripts\demo.cmd stop       REM kill everything
```

### Windows — PowerShell

```powershell
# PowerShell 7+ (pwsh):
pwsh -File scripts/demo.ps1                    # backend + simulator
pwsh -File scripts/demo.ps1 -WithBot           # ...also launches Discord bot
pwsh -File scripts/demo.ps1 -Stop              # stop everything

# Or Windows PowerShell 5.x (powershell):
powershell -File scripts\demo.ps1
powershell -File scripts\demo.ps1 -WithBot
powershell -File scripts\demo.ps1 -Stop
```

### Linux / macOS (bash)

```bash
./scripts/demo.sh              # backend + simulator
./scripts/demo.sh --with-bot   # ...also launches Discord bot
./scripts/demo.sh --stop       # stop everything
```

Then open:

- **Backend API docs** → <http://127.0.0.1:8000/docs>
- **Frontend** → run `cd frontend && npm run dev`, then open <http://localhost:3000>

The simulator drives 15 devices, alternating ON/OFF at staggered 3s / 5s / 7s
intervals per room, and POSTs to `/api/ingest`. The frontend updates in real
time via WebSocket.

---

## 1. Setup (if not using the demo script)

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

# Backend env (one-time)
copy backend\.env.example backend\.env

# Optional: bot env (one-time)
copy bot\.env.example bot\.env
# ...then edit bot/.env with your DISCORD_TOKEN + ALERT_CHANNEL_ID
```

For a fast demo, edit `backend/.env` to shrink the duration threshold:

```env
DURATION_THRESHOLD_SECONDS=20
```

This makes the "all devices in one room ON for too long" alert fire within
~30 seconds.

---

## 2. Run Manually (Three Terminals)

Terminal 1 — **Backend**:

```powershell
uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```

Terminal 2 — **Simulator**:

```powershell
python -m simulator.simulator
```

Terminal 3 — **Frontend**:

```powershell
cd frontend
npm run dev
```

Optional Terminal 4 — **Discord bot**:

```powershell
python -m bot.bot
```

---

## 3. Demo Checklist (5-minute walk-through)

1. **Show the simulator running** — point at Terminal 2, explain that it
   emulates 15 devices with staggered intervals.

2. **Open the frontend** — <http://localhost:3000>. Within 5–10 seconds,
   fans start spinning and lights start glowing as the simulator toggles
   devices. The total wattage in the top card animates.

3. **Show REST reads stay in sync**:

   ```powershell
   Invoke-RestMethod http://127.0.0.1:8000/api/status
   Invoke-RestMethod http://127.0.0.1:8000/api/usage
   ```

4. **Demo an off-hours alert** — set `OFFICE_END` and `OFFICE_START` in
   `backend/.env` to bracket a window that excludes right now (e.g.
   `OFFICE_START=23:59`, `OFFICE_END=23:59`). Restart the backend. The
   next time the simulator turns a device ON, an off-hours alert fires on
   `/ws/alerts`.

5. **Demo a room-duration alert** — with `DURATION_THRESHOLD_SECONDS=20`,
   wait for the simulator to land all 5 devices in one room ON simultaneously.
   Within ~30 s the room-duration alert fires.

6. **Show the Discord bot** (if running) — type `!status`, `!room Drawing
   Room`, `!usage` in your Discord channel. Show the bot posting alerts to
   the alert channel when rules fire.

7. **Show the engine code paths**:

   ```
   backend/app/ingest.py       — ingestion gateway
   backend/app/state.py        — hot state
   backend/app/alerts.py       — alert engine (dual path)
   backend/app/persistence/    — SQLite cold state
   backend/app/websocket/      — WS managers
   simulator/simulator.py      — synthetic data source
   frontend/                   — Next.js frontend
   ```

---

## 4. Manual API Tests (curl / PowerShell)

```powershell
# Ingest a state change
curl.exe -X POST "http://127.0.0.1:8000/api/ingest" `
  -H "Content-Type: application/json" `
  --data-binary "@examples/ingest_state_change.json"

# Or single-quoted inline JSON
curl.exe -X POST "http://127.0.0.1:8000/api/ingest" `
  -H "Content-Type: application/json" `
  -d '{"message_type":"state_change","source_id":"esp32-work-room-1","sequence":1,"device_timestamp":"2026-07-04T14:00:30Z","changes":[{"device_id":"work_room_1_fan_1","room":"work_room_1","device_type":"fan","status":"on","power_draw_w":60}]}'

# Read state
Invoke-RestMethod http://127.0.0.1:8000/api/status
Invoke-RestMethod "http://127.0.0.1:8000/api/room/Drawing%20Room"
Invoke-RestMethod http://127.0.0.1:8000/api/usage
```

---

## 5. Talking Points (judges, audience)

- **FastAPI is the single source of truth** — same REST and WebSocket
  endpoints power both the frontend and the Discord bot. They cannot drift.
- **Dual-path alerting** — event-driven on every ingest, plus a 30 s periodic
  sweep so time-only breaches are still caught even if no device event fires.
- **De-duplication** — a partial unique index on `alert_log` ensures only one
  unresolved alert per `(alert_type, target)` pair at a time. Auto-resolves
  when the condition clears.
- **Server-side timestamping** — eliminates clock skew between simulator and
  backend.
- **Open schema** — same JSON contract a real ESP32 would send; the simulator
  and any future hardware swap is a one-line change.

---

## 6. Related Documents

- [`SYSTEM_GUIDE.md`](./SYSTEM_GUIDE.md) — full system reference
- [`SIMULATOR.md`](./SIMULATOR.md) — simulator internals
- [`HARDWARE.md`](./HARDWARE.md) — reference schematic for a future ESP32
- [`DISCORD_BOT_SETUP.md`](../DISCORD_BOT_SETUP.md) — bot setup
