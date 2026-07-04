# High-Level System Diagrams (Phase 3 Complete)

These diagrams assume **Phase 3 is fully implemented**: `simulator.py` is running, the web dashboard frontend is live, and device state flows end to end from simulation to both the Discord bot and the live dashboard.

Two versions are shown:

| Version | Hot state | Cold state | When to use |
|---|---|---|---|
| **Version 1** | In-memory dict | SQLite | Current repo — simple local setup, zero extra infra |
| **Version 2** | Redis | PostgreSQL | Production-scale — persistence across restarts, multi-instance backend |

---

## Version 1 — In-Memory + SQLite (Current Stack)

No Redis. No PostgreSQL. Matches what is implemented today, extended with the Phase 3 simulator and dashboard frontend.

### System overview

```mermaid
flowchart TB
    subgraph hardware [Reference Only]
        Wokwi["Wokwi / Tinkercad Schematic\n1 room, ESP32 + relays\n(not runtime)"]
    end

    subgraph edge [Edge Simulation Layer]
        Sim["simulator.py\n15 devices, 3 rooms\nstaggered POST 3s / 5s / 7s"]
    end

    subgraph backend [Central Hub — FastAPI :8000]
        Ingest["POST /api/ingest\nstamp last_changed"]
        Hot["Hot State\nin-memory dict\n15 devices"]
        Cold["Cold State\nSQLite\ntransitions + alerts + kWh"]
        Engine["Alert Engine\nevent-driven + 30s sweep"]
        REST["REST /api/status\n/api/room /api/usage"]
        WSAlert["WS /ws/alerts"]
        WSDash["WS /ws/dashboard"]
    end

    subgraph clients [Client Layer]
        Dash["Web Dashboard\nlive SVG / DOM\npower meter + alerts"]
        Bot["Discord Bot\ndiscord.py"]
    end

    subgraph users [Users]
        WebUser["User in browser"]
        DiscordUser["User in Discord"]
    end

    Wokwi -.->|"concept only"| Sim
    Sim -->|"heartbeat / state_change JSON"| Ingest
    Ingest --> Hot
    Ingest --> Cold
    Ingest --> Engine
    Engine --> Cold
    Engine --> WSAlert
    Hot --> REST
    Hot --> WSDash
    Cold --> REST
    Ingest --> WSDash

    WSDash -->|"state_diff push"| Dash
    WSAlert -->|"Alert JSON push"| Bot
    REST -->|"pull on command"| Bot

    Dash --> WebUser
    Bot -->|"!status !room !usage\n+ proactive alerts"| DiscordUser
```

### Full information flow — device state to user

End-to-end path when a device toggles ON in the simulator:

```mermaid
sequenceDiagram
    autonumber
    participant Sim as simulator.py
    participant Ingest as POST /api/ingest
    participant Hot as Hot State memory
    participant DB as SQLite
    participant Alerts as Alert Engine
    participant WSD as WS /ws/dashboard
    participant WSA as WS /ws/alerts
    participant Dash as Web Dashboard
    participant REST as REST /api/*
    participant Bot as Discord Bot
    participant WebUser as Browser User
    participant DCUser as Discord User

    Note over Sim: Device toggles ON in Drawing Room
    Sim->>Ingest: state_change JSON device_id status power_draw_w

    Ingest->>Ingest: Stamp last_changed server UTC
    Ingest->>Hot: apply_updates
    Ingest->>DB: log_transition append-only
    Ingest->>Alerts: evaluate_on_ingest

    alt Rule breached off-hours or room duration
        Alerts->>DB: create_alert deduplicated
        Alerts->>WSA: broadcast Alert
        WSA->>Bot: WebSocket push
        Bot->>DCUser: Post alert to channel optional LLM rewrite
    end

    Ingest->>WSD: broadcast_diff changes totals
    WSD->>Dash: state_diff JSON
    Dash->>Dash: Update fan spin light glow power meter
    Dash->>WebUser: Live UI update no refresh

    Note over DCUser: User types !status
    DCUser->>Bot: !status
    Bot->>REST: GET /api/status
    REST->>Hot: get_office_status
    Hot-->>REST: OfficeStatus JSON
    REST-->>Bot: APIResponse
    Bot->>DCUser: Friendly reply optional LLM
```

### Data stores — Version 1

```mermaid
flowchart LR
    subgraph hot [Hot State — RAM]
        D1["device_id to status power_draw_w last_changed"]
    end

    subgraph cold [Cold State — SQLite file]
        T["state_transitions\nappend-only log"]
        A["alert_log\nhistory + dedup"]
    end

    Ingest["Ingestion"] --> hot
    Ingest --> T
    Alerts["Alerts"] --> A
    REST["REST reads"] --> hot
    REST --> T
    Usage["kWh calc"] --> T
```

---

## Version 2 — Redis + PostgreSQL (Full Stack)

All components implemented including Redis for hot state and PostgreSQL for cold state. Supports backend restarts without losing live state and horizontal scaling of FastAPI workers.

### System overview

```mermaid
flowchart TB
    subgraph hardware [Reference Only]
        Wokwi["Wokwi / Tinkercad Schematic\n1 room, ESP32 + relays\n(not runtime)"]
    end

    subgraph edge [Edge Simulation Layer]
        Sim["simulator.py\n15 devices, 3 rooms\nstaggered POST 3s / 5s / 7s"]
    end

    subgraph backend [Central Hub — FastAPI :8000]
        Ingest["POST /api/ingest\nstamp last_changed"]
        Engine["Alert Engine\nevent-driven + 30s sweep"]
        REST["REST /api/status\n/api/room /api/usage"]
        WSAlert["WS /ws/alerts"]
        WSDash["WS /ws/dashboard"]
    end

    subgraph persistence [Persistence Layer]
        Redis["Redis\nHot State\ncurrent device status + wattage\nTTL optional pub/sub"]
        PG["PostgreSQL\nCold State\nstate_transitions\nalert_log\nusage aggregates"]
    end

    subgraph clients [Client Layer]
        Dash["Web Dashboard\nlive SVG / DOM\npower meter + alerts"]
        Bot["Discord Bot\ndiscord.py"]
    end

    subgraph users [Users]
        WebUser["User in browser"]
        DiscordUser["User in Discord"]
    end

    Wokwi -.->|"concept only"| Sim
    Sim -->|"heartbeat / state_change JSON"| Ingest
    Ingest --> Redis
    Ingest --> PG
    Ingest --> Engine
    Engine --> PG
    Engine --> WSAlert
    Redis --> REST
    Redis --> WSDash
    PG --> REST
    Ingest --> WSDash

    WSDash -->|"state_diff push"| Dash
    WSAlert -->|"Alert JSON push"| Bot
    REST -->|"pull on command"| Bot

    Dash --> WebUser
    Bot -->|"!status !room !usage\n+ proactive alerts"| DiscordUser
```

### Full information flow — device state to user

```mermaid
sequenceDiagram
    autonumber
    participant Sim as simulator.py
    participant Ingest as POST /api/ingest
    participant Redis as Redis Hot State
    participant PG as PostgreSQL
    participant Alerts as Alert Engine
    participant WSD as WS /ws/dashboard
    participant WSA as WS /ws/alerts
    participant Dash as Web Dashboard
    participant REST as REST /api/*
    participant Bot as Discord Bot
    participant WebUser as Browser User
    participant DCUser as Discord User

    Note over Sim: Device toggles ON in Work Room 1
    Sim->>Ingest: state_change JSON

    Ingest->>Ingest: Stamp last_changed server UTC
    Ingest->>Redis: HSET device_id status power_draw_w last_changed
    Ingest->>PG: INSERT state_transitions
    Ingest->>Alerts: evaluate_on_ingest

    alt Rule breached
        Alerts->>PG: INSERT alert_log ON CONFLICT dedup
        Alerts->>WSA: broadcast Alert
        WSA->>Bot: WebSocket push
        Bot->>DCUser: Alert in Discord channel
    end

    Ingest->>WSD: broadcast_diff
    WSD->>Dash: state_diff JSON
    Dash->>WebUser: Live dashboard update

    Note over DCUser: User types !room Work Room 1
    DCUser->>Bot: !room Work Room 1
    Bot->>REST: GET /api/room/Work Room 1
    REST->>Redis: read all devices in room
    REST-->>Bot: Room JSON
    Bot->>DCUser: Friendly reply

    Note over WebUser: Dashboard open in browser
    WebUser->>Dash: Page load then WS connect
    Dash->>WSD: Subscribe /ws/dashboard
    Note over Dash,WebUser: Subsequent ingests push diffs automatically
```

### Data stores — Version 2

```mermaid
flowchart LR
    subgraph hot [Hot State — Redis]
        R["HASH per device_id\nstatus power_draw_w last_changed room"]
        Pub["optional PUBLISH\nstate_updates channel"]
    end

    subgraph cold [Cold State — PostgreSQL]
        T["state_transitions\ntime-series indexed"]
        A["alert_log\npartial unique unresolved"]
        V["materialized views\noptional daily kWh rollup"]
    end

    Ingest["Ingestion"] --> R
    Ingest --> T
    R --> Pub
    Alerts["Alerts"] --> A
    REST["REST reads"] --> R
    REST --> T
    REST --> V
```

---

## Side-by-Side Comparison

```mermaid
flowchart TB
    subgraph v1 [Version 1 — Current]
        direction TB
        S1[simulator.py] --> B1[FastAPI]
        B1 --> M1[Memory Hot State]
        B1 --> Q1[SQLite Cold State]
        B1 --> D1[Dashboard WS]
        B1 --> Bot1[Discord Bot]
    end

    subgraph v2 [Version 2 — Full Stack]
        direction TB
        S2[simulator.py] --> B2[FastAPI]
        B2 --> R2[Redis Hot State]
        B2 --> P2[PostgreSQL Cold State]
        B2 --> D2[Dashboard WS]
        B2 --> Bot2[Discord Bot]
    end
```

| Aspect | Version 1 | Version 2 |
|---|---|---|
| Hot state | In-memory Python dict | Redis hashes |
| Cold state | SQLite file on disk | PostgreSQL server |
| Backend restart | Hot state resets to manifest defaults | Hot state survives in Redis |
| Multi-worker FastAPI | Shared state requires sticky sessions or single worker | Redis shared across workers |
| Setup complexity | Minimal — `pip install` + run | Requires Redis + Postgres services |
| Best for | Hackathon, local dev, demos | Production, multi-instance deployment |

---

## Communication Channels (Both Versions)

Both versions use the same **client-facing protocol** — only the persistence layer differs.

```mermaid
flowchart LR
    subgraph push [Push — real-time]
        WSD["WS /ws/dashboard\nstate_diff after ingest"]
        WSA["WS /ws/alerts\nAlert on rule breach"]
    end

    subgraph pull [Pull — on demand]
        REST["REST /api/status\n/api/room /api/usage"]
    end

    Backend["FastAPI Backend"] --> WSD
    Backend --> WSA
    Backend --> REST

    WSD --> Dashboard["Web Dashboard"]
    WSA --> BotAlert["Discord Bot\nalert listener"]
    REST --> BotCmd["Discord Bot\ncommands"]

    Dashboard --> WebUser["Browser user\nlive updates"]
    BotAlert --> DiscordUser["Discord user\nproactive alerts"]
    BotCmd --> DiscordUser
```

| Channel | Direction | Consumer | Payload |
|---|---|---|---|
| `POST /api/ingest` | Simulator → Backend | Ingestion gateway | `heartbeat` or `state_change` |
| `WS /ws/dashboard` | Backend → Dashboard | Browser | `state_diff` with changes + wattage totals |
| `WS /ws/alerts` | Backend → Discord bot | Bot alert task | `Alert` JSON (id, message, severity, created_at) |
| `GET /api/status` | Discord bot → Backend | On `!status` | `OfficeStatus` envelope |
| `GET /api/room/{name}` | Discord bot → Backend | On `!room` | `Room` envelope |
| `GET /api/usage` | Discord bot → Backend | On `!usage` | `Usage` envelope (from cold store) |

---

## Device → User Journey (Narrative)

This is the story both diagrams tell:

1. **Device state changes** in `simulator.py` (or a future real ESP32) — e.g. `work_room_1_fan_1` turns ON at 60W.
2. **Simulator sends JSON** to `POST /api/ingest` as a `state_change` payload.
3. **Backend stamps time**, writes to hot state (memory or Redis) and cold store (SQLite or PostgreSQL).
4. **Alert engine evaluates** rules immediately; periodic sweep catches time-only breaches.
5. **Dashboard path (push):** `/ws/dashboard` broadcasts a `state_diff` → frontend updates fan animation and power meter → **browser user sees live change**.
6. **Alert path (push):** if a rule fires → `/ws/alerts` pushes `Alert` JSON → Discord bot posts to alert channel → **Discord user sees proactive warning**.
7. **Command path (pull):** Discord user types `!status` → bot calls `GET /api/status` → reads hot state → LLM optionally rewrites → **Discord user sees current summary**.

---

## Related Documents

- [ARCHITECTURE.md](./ARCHITECTURE.md) — Design decisions and implementation status (Version 1)
- [SYSTEM_GUIDE.md](./SYSTEM_GUIDE.md) — How to run and test today
- [SIMULATOR.md](./SIMULATOR.md) — Phase 3 simulator guide
- [README.md](../README.md) — Onboarding and local setup
