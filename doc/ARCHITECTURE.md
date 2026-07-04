# Architecture Document: Office Energy Monitoring System

**Version:** 2.1  
**Status:** Backend, ingestion, alerts, SQLite, real WebSockets, simulator, and Next.js frontend are live.

**Changelog from v2.0:** Updated to reflect Phase 2 implementation (15 devices, in-memory hot state, SQLite cold state, `RealBotRepository`, dual-path alerting, ingestion gateway). Corrected device count. Added implementation status, actual repository layout, and links to onboarding docs.

---

## 1. Design Philosophy

The system is a modular, event-driven architecture centered on a FastAPI backend that acts as the **single source of truth** for all device state. Two independent triggers feed the alerting engine — **state-change events** and a **periodic time sweep** — because some alert conditions (like "it's now past 5 PM") aren't caused by a device event at all; they're caused by the clock moving.

Visualization favors low-latency delivery: WebSockets push updates to the frontend, and the Discord bot pulls from the same REST layer the frontend uses, so both interfaces reflect identical state.

---

## 2. Implementation Status

| Component | Status | Location |
|---|---|---|
| Shared Pydantic API contracts | Done (Phase 1) | `shared/models/` |
| FastAPI REST (`/api/status`, `/api/room`, `/api/usage`, `/api/health`) | Done | `iut_server/app/api/bot.py` |
| Ingestion gateway (`POST /api/ingest`) | Done (Phase 2) | `iut_server/app/api/ingest.py` |
| Hot state (in-memory, 15 devices) | Done (Phase 2) | `iut_server/app/state.py` |
| Cold state (SQLite transitions + alerts) | Done (Phase 2) | `iut_server/app/persistence/` |
| RealBotRepository + kWh calculation | Done (Phase 2) | `iut_server/app/repositories/real_repository.py` |
| Dual-path alert engine | Done (Phase 2) | `iut_server/app/alerts.py` |
| Alert WebSocket (`/ws/alerts`) | Done (Phase 2) | `iut_server/app/websocket/manager.py` |
| Live state WebSocket (`/ws/live`) | Done | `iut_server/app/websocket/live_state.py` |
| Discord bot (commands + alert listener) | Done (Phase 1) | `bot/` |
| Groq LLM integration | Done (Phase 1) | `bot/services/llm_client.py` |
| `simulator.py` | Implemented (Phase 3) | `simulator/simulator.py` |
| Next.js frontend | Implemented | `frontend/` |
| Redis / PostgreSQL | Deferred | — |

---

## 3. High-Level System Architecture

```text
[ Wokwi/Tinkercad ]         Reference schematic only (1 room, not runtime data)

[ Python Simulator ]        Phase 3 — emulates 15 devices
  |  Staggered POSTs: Drawing Room 3s, Work Room 1 5s, Work Room 2 7s
  |  Sends heartbeat + state_change JSON on toggle
  v
[ Central Hub (FastAPI) :8000 ]
  |  POST /api/ingest — stamps last_changed server-side
  |  Computes total/per-room wattage
  |  Event-driven alert check on every ingest
  |  Periodic alert sweep every 30s (asyncio background task)
  |
  |---> [ In-memory Hot State ]     15 devices keyed by device_id
  |---> [ SQLite Cold State ]       state_transitions + alert_log
  |
  |--- WS /ws/live ---------------> [ Next.js Frontend ]
  |
  +--- REST /api/* -----------------> [ Discord Bot ]
  |       !status, !room, !usage
  |
  +--- WS /ws/alerts ---------------> [ Discord Bot alert channel ]
```

### Data flow (ingestion)

```text
POST /api/ingest
  -> validate JSON (heartbeat | state_change)
  -> stamp last_changed (server UTC)
  -> update HotStateStore
  -> append state_transitions (SQLite)
  -> evaluate_on_ingest() (alerts)
  -> broadcast_diff() (/ws/live)
  -> return { accepted, updated }
```

---

## 4. Device Inventory

**15 devices** across 3 rooms (2 fans + 3 lights per room).

| Room slug | Display name | Device IDs |
|---|---|---|
| `drawing_room` | Drawing Room | `drawing_room_fan_1`, `drawing_room_fan_2`, `drawing_room_light_1..3` |
| `work_room_1` | Work Room 1 | `work_room_1_fan_1`, `work_room_1_fan_2`, `work_room_1_light_1..3` |
| `work_room_2` | Work Room 2 | `work_room_2_fan_1`, `work_room_2_fan_2`, `work_room_2_light_1..3` |

Ingestion uses lowercase `on`/`off` and snake_case room slugs. The REST API exposes display names (`Drawing Room`) and `ON`/`OFF` enum values via shared models without modification.

---

## 5. Component Breakdown

### A. Edge Simulation Layer

- **Hardware schematic (Wokwi/Tinkercad):** Reference only — ESP32 + relays for 2 fans and 3 lights in one room. Not wired to runtime.
- **Runtime simulator (`simulator/simulator.py`):** Phase 3. Will POST to `/api/ingest` with probabilistic toggles and staggered room intervals. See [SIMULATOR.md](./SIMULATOR.md).
- **Manual testing (Phase 2):** `curl` / `Invoke-RestMethod` or JSON files in `examples/`.

### B. Central Hub (FastAPI)

| Module | Responsibility |
|---|---|
| `iut_server/app/api/ingest.py` | Ingestion gateway |
| `iut_server/app/state.py` | Hot state store + device manifest |
| `iut_server/app/persistence/` | SQLite cold state |
| `iut_server/app/alerts.py` | Event-driven + periodic alert evaluation |
| `iut_server/app/repositories/real_repository.py` | Bot-facing reads from hot state + usage from SQLite |
| `iut_server/app/api/bot.py` | REST endpoints for Discord bot |
| `iut_server/app/api/websocket.py` | `/ws/alerts`, `/ws/live` |

**Communication channels:**

1. **Live state WebSocket** (`/ws/live`) — broadcasts state diffs after each ingest.
2. **Bot REST API** (`/api/status`, `/api/room`, `/api/usage`) — pull-only; bot does not subscribe to state broadcast.
3. **Alert Event Stream** (`/ws/alerts`) — proactive alerts only; separate from bot REST so FastAPI never holds Discord credentials.

### C. Intelligence Layer (LLM)

- **Workflow:** Discord command → bot fetches JSON via REST → Groq LLM → conversational reply.
- **Fallback:** Deterministic formatted text when Groq is unavailable or `LLM_ENABLED=false`.
- **Alerts:** Incoming WebSocket alerts can also be rewritten by the LLM before posting.

### D. Persistence Layer

| Layer | Technology | Purpose |
|---|---|---|
| **Hot state** | In-memory `dict[str, DeviceRecord]` | Real-time status, wattage, alert duration checks |
| **Cold state** | SQLite (`data/office_energy.db`) | Transition log, alert history, kWh integration, de-duplication |

Redis was evaluated and deferred — 15 devices do not justify the operational overhead at this scale.

---

## 6. Core Logic: Alerting Engine

**File:** `iut_server/app/alerts.py`

### 6.1 Alert Rules

| Rule | Condition | Target | Implemented |
|---|---|---|---|
| **Off-Hours Alert** | Device `on` outside `OFFICE_START`–`OFFICE_END` | `device_id` | Yes |
| **Room Duration Alert** | All devices in room `on` continuously > `DURATION_THRESHOLD` | room slug | Yes |
| **Device Duration Alert** | Single device `on` > `DEVICE_DURATION_THRESHOLD_SECONDS` | `device_id` | Yes (Phase 3) |

### 6.2 Two Evaluation Paths

**1. Event-driven** — runs in the ingest handler after `apply_updates()`:
- Off-hours check for each changed device now `on`
- Room duration check for each affected room

**2. Periodic sweep** — `asyncio` background task every `ALERT_SWEEP_INTERVAL_SECONDS` (default 30):
- Full scan of all devices and rooms
- Catches clock-crossing conditions (e.g. office hours end while device stays on)

### 6.3 De-duplication and Resolution

- Before firing: check SQLite `alert_log` for unresolved alert with same `alert_type` + `target`.
- Partial unique index: `UNIQUE(alert_type, target) WHERE resolved_at IS NULL`.
- Auto-resolve when condition clears (device off, office hours resume, any room device off).

---

## 7. Communication Strategy

| Consumer | Transport | Endpoints |
|---|---|---|
| Discord bot commands | REST | `GET /api/status`, `/api/room/{name}`, `/api/usage` |
| Discord proactive alerts | WebSocket | `WS /ws/alerts` |
| Next.js frontend | WebSocket | `WS /ws/live` |
| Simulator / manual test | REST | `POST /api/ingest` |

---

## 8. Configuration and Demo Mode

**File:** `iut_server/app/config.py` — loaded from `iut_server/.env`

| Variable | Default | Purpose |
|---|---|---|
| `OFFICE_START` | `09:00` | Office hours start |
| `OFFICE_END` | `17:00` | Office hours end |
| `DURATION_THRESHOLD_SECONDS` | `7200` | Room all-ON alert threshold |
| `DEVICE_DURATION_THRESHOLD_SECONDS` | `3600` | Per-device ON alert threshold (`0` fires immediately on every ingest) |
| `ALERT_SWEEP_INTERVAL_SECONDS` | `30` | Periodic sweep interval |
| `SQLITE_PATH` | `data/office_energy.db` | SQLite database path |

**Demo mode example** (`iut_server/.env`):

```env
DURATION_THRESHOLD_SECONDS=20
DEVICE_DURATION_THRESHOLD_SECONDS=0
```

Restart the backend after changing env vars.

---

## 9. Engineering Trade-offs

| Decision | Rationale |
|---|---|
| Python simulator over Wokwi runtime | Reliable multi-room demo data; schematic stays a hardware deliverable |
| In-memory hot state | Fast, zero infra; sufficient for 15 devices |
| SQLite cold state | Append-only log for kWh and duration; no external DB |
| Separate alert WebSocket | FastAPI never holds Discord token or rate limits |
| Server-side timestamping | Eliminates clock skew between simulator and server |
| Dual-path alerting | Event-only misses time-based threshold crossings |
| `MockBotRepository` retained | Phase 1 unit tests; production uses `RealBotRepository` |

---

## 10. Validation Approach

1. `POST /api/ingest` state change → `GET /api/status` reflects new wattage within the same request cycle.
2. `!status` in Discord matches `/api/status` JSON.
3. Set `DURATION_THRESHOLD_SECONDS=20`, turn all devices in one room ON → room duration alert within ~30s on `/ws/alerts` and Discord.
4. Set `OFFICE_END` so current time is outside hours, leave device ON → off-hours alert from periodic sweep without new ingest.
5. Leave breach active across multiple sweeps → only one unresolved alert per type/target in SQLite.
6. Simulator running → frontend and Discord stay in sync without manual curl.

---

## 11. Repository Structure (actual)

```text
/
├── README.md                      # Onboarding and quick start
├── doc/
│   ├── ARCHITECTURE.md            # This document
│   ├── SYSTEM_GUIDE.md            # How the system works + testing
│   └── SIMULATOR.md               # Phase 3 simulator guide
├── shared/models/                 # Pydantic API contracts (shared by backend + bot)
├── iut_server/app/
│   ├── main.py                    # App factory, lifespan, sweep task
│   ├── config.py                  # Env-based settings
│   ├── state.py                   # Hot state + 15-device manifest
│   ├── alerts.py                  # Alert engine
│   ├── persistence/               # SQLite (models.py, database.py)
│   ├── schemas/ingestion.py       # Backend-only ingest payloads
│   ├── api/
│   │   ├── bot.py                 # REST for Discord
│   │   ├── ingest.py              # POST /api/ingest
│   │   └── websocket.py           # /ws/alerts, /ws/live
│   ├── repositories/
│   │   ├── mock_repository.py     # Phase 1 tests
│   │   └── real_repository.py     # Phase 2 production
│   ├── services/bot_service.py
│   └── websocket/                 # Connection managers
├── bot/                           # Discord bot
├── examples/                      # Sample ingest JSON payloads
├── tests/
└── simulator/                     # Phase 3 (not yet implemented)
```

---

## 12. Related Documents

- [HIGH_LEVEL_DIAGRAMS.md](./HIGH_LEVEL_DIAGRAMS.md) — Phase 3 system diagrams (memory/SQLite vs Redis/PostgreSQL)
- [README.md](../README.md) — Local setup and onboarding
- [SYSTEM_GUIDE.md](./SYSTEM_GUIDE.md) — End-to-end flows, diagrams, and test procedures
- [SIMULATOR.md](./SIMULATOR.md) — `simulator.py` implementation guide
- [HARDWARE.md](./HARDWARE.md) — ESP32 + relay reference schematic
- [DEMO.md](./DEMO.md) — Live demo walk-through
- [DISCORD_BOT_SETUP.md](../DISCORD_BOT_SETUP.md) — Discord Developer Portal setup
