# Architecture Overview

The full system architecture is documented in **[doc/ARCHITECTURE.md](doc/ARCHITECTURE.md)**.

## Current Phase: 2 (Backend + Bot)

```text
[ curl / simulator Phase 3 ]
         |
         v POST /api/ingest
[ FastAPI Backend :8000 ]
  |-- Hot State (in-memory, 15 devices)
  |-- SQLite (transitions, alerts, kWh)
  |-- Alert Engine (event + 30s sweep)
  |
  |-- REST /api/* --------> Discord Bot (!status, !room, !usage)
  |-- WS /ws/alerts ------> Discord Bot (proactive alerts)
  `-- WS /ws/live --------> Next.js Frontend
```

## Layering

| Layer | Role |
|---|---|
| `shared/models/` | Pydantic API contracts shared by backend and bot |
| `backend/app/api/` | HTTP and WebSocket routes |
| `backend/app/services/` | Business coordination (`BotService`) |
| `backend/app/repositories/` | Data access (`RealBotRepository` in production) |
| `backend/app/state.py` | In-memory hot state |
| `backend/app/persistence/` | SQLite cold state |
| `backend/app/alerts.py` | Dual-path alerting |
| `bot/` | Discord commands, API client, LLM client, alert listener |

## Phase History

| Phase | Scope |
|---|---|
| **1** | Mock backend, Discord bot, shared models, mock alert WebSocket |
| **2** | Real ingestion, hot/cold state, alert engine, `RealBotRepository`, kWh usage |
| **3** | `simulator.py`, Next.js frontend |

See [doc/ARCHITECTURE.md](doc/ARCHITECTURE.md) for design decisions, alert rules, configuration, and validation checklist.
