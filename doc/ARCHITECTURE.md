# Architecture Document: Office Energy Monitoring System

**Version:** 2.0
**Status:** Approved for Implementation
**Changelog from v1.1:** Fixed after-hours alert window (was "after 5PM only," now correctly "outside 9AM–5PM"), added a periodic time-based alert scheduler (event-driven checks alone cannot catch clock-crossing conditions), resolved the room-vs-device duration alert ambiguity, standardized bot data-fetch transport to REST, and added configuration/demo-mode guidance.

---

## 1. Design Philosophy

The system is a modular, event-driven architecture centered on a FastAPI backend that acts as the single source of truth for all device state. Two independent triggers feed the alerting engine — **state-change events** and a **periodic time sweep** — because some alert conditions (like "it's now past 5 PM") aren't caused by a device event at all; they're caused by the clock moving. Visualization favors low-latency delivery: WebSockets push updates to the dashboard, and the Discord bot pulls from the same REST layer the dashboard's backend uses, so both interfaces are guaranteed to reflect identical state.

---

## 2. High-Level System Architecture Diagram

*(This ASCII block is for planning only. The final deliverable diagram must be produced in Excalidraw, draw.io, or hand-drawn — Mermaid is explicitly disallowed by the brief.)*

```text
[ Wokwi/Tinkercad ]         (Reference Schematic Only — 1 room, not runtime data)

[ Python Simulator ]        (simulator.py — emulates 18 devices)
  |  - Staggered POSTs: Drawing Room 3s, Work Room 1 5s, Work Room 2 7s
  |  - Sends state changes + wattage on toggle
  v
[ Central Hub (FastAPI) ]
  |  - Ingests JSON, stamps last_changed server-side
  |  - Computes total/per-room wattage
  |  - Event-driven check: runs alert rules on every state update
  |  - Periodic check: background sweep every 30s for time-based rules
  |
  |---> [ In-memory / Redis state ]   (Hot State: current status + wattage per device)
  |---> [ SQLite Database ]           (Cold State: state-transition log, alert history, kWh)
  |
  |--- (WebSocket: State Broadcast) ---> [ Web Dashboard ]
  |                                        - Live Device Status Panel
  |                                        - Live Power Meter (total + per-room)
  |                                        - Top-View Animated Layout (bonus)
  |                                        - Active Alerts Panel
  |
  +--- (REST: Data Fetch) --------------> [ Discord Bot (discord.py) ]
  |                                        - !status, !room <name>, !usage
  |                                        - Bot → FastAPI REST → JSON → LLM → reply
  |
  +--- (WebSocket/SSE: Alert Stream) ---> [ Discord Bot ]
                                             - Receives proactive alert events
                                             - Posts to designated Discord channel
```

---

## 3. Component Breakdown

### A. Edge Simulation Layer
Separates the physical schematic (a project deliverable) from the runtime data source (what actually drives the demo).

- **Hardware Schematic (Wokwi/Tinkercad):** A representative circuit for *one room only* — ESP32 + relays/current sensors for 2 fans and 3 lights. Concept/reference only; never wired to the running system.
- **Runtime Simulator (`simulator.py`):** Standalone script emulating all 18 devices across 3 rooms. Generates JSON payloads on state change (not on every tick — see below).
- **Staggered reporting:** Drawing Room every 3s, Work Room 1 every 5s, Work Room 2 every 7s. Purely cosmetic for the demo — makes rooms visibly update independently rather than all at once.
- **State-change logic:** The simulator should toggle devices probabilistically (e.g., small random chance per tick) rather than on a fixed schedule, so the demo looks organic. This should be explicitly implemented and documented, not left implicit.

### B. Central Hub (FastAPI)
The single source of truth for both interfaces.

- **Ingestion Gateway:** REST endpoint(s) receive state JSON from `simulator.py`. The server — not the simulator — stamps `last_changed`, eliminating clock-skew between simulator and server.
- **Logic Engine:** Recomputes total/per-room wattage on ingestion. Two independent alert-evaluation paths (detailed in Section 4).
- **Communication channels:**
  1. **Dashboard WebSocket** — broadcasts raw state diffs to connected web clients.
  2. **Bot REST API** — endpoints for `!status`, `!room`, `!usage`; the bot pulls, it does not subscribe to the state broadcast.
  3. **Alert Event Stream** — WebSocket/SSE endpoint the Discord bot subscribes to for proactive alerts only. Kept separate from the Bot REST API so the bot's Discord token and posting logic never live inside FastAPI.

### C. Intelligence Layer (LLM)
- **Workflow:** Discord query → bot fetches raw JSON via REST → JSON + system prompt → LLM → conversational reply → posted to Discord.
- **System prompt constraint:** e.g. *"You are a friendly office assistant. Summarize this device JSON in 1–2 sentences. Never dump raw JSON or field names."* This is what prevents robotic responses, per the brief's explicit requirement.

### D. Persistence Layer
- **Hot state (current status per device):** In-memory dict is sufficient for 18 devices; Redis is a valid upgrade but adds infra risk for a hackathon timeline without a clear payoff at this scale — pick based on how much time you have, not because bigger is better.
- **Cold state (SQLite):** State-transition log. Required for computing continuous-ON duration (Section 4) and for summing wattage-over-time into `!usage`'s daily kWh figure.

---

## 4. Core Logic: Alerting Engine

This is the section that changed most from v1.1. **Two independent triggers** feed the same alert-creation path — relying on state-change events alone will silently miss both rules below, because both are triggered by the clock, not by a device toggling.

### 4.1 Alert Rules

| Rule | Condition | Trigger type |
|---|---|---|
| **Off-Hours Alert** | Any device is `ON` while current server time is outside **9:00–17:00** | Time-based |
| **Room Duration Alert** *(spec-compliant, primary)* | *All* devices in a room have been continuously `ON` for **> 2 hours** | Time-based |
| **Device Duration Alert** *(enhancement, optional)* | A single device has been continuously `ON` for **> 2 hours** | Time-based |

> **Note on the duration rule:** The brief's example is room-level ("a room where all devices have been on for more than 2 hours continuously"). v1.1 drifted to a per-device rule, which is a different condition. This version implements the room-level rule as the spec-compliant minimum, with per-device duration tracking kept as an optional enhancement since it's more granular and useful for the dashboard's per-device view — but it should be clearly labeled as beyond-spec if you demo it, so graders don't think you misread the requirement.

### 4.2 Two Evaluation Paths

**1. Event-driven check** — runs inside the ingestion handler, on every state update:
- Cheap conditions that *can* change because of the event itself (e.g., "did this specific device just cross into ON while it's already after hours").
- Cannot alone catch a device that was already ON before the threshold was crossed.

**2. Periodic sweep** — a background task (`asyncio` loop or APScheduler), ticking independently of any incoming data:

```python
# Runs every 30s regardless of whether any device event has occurred
async def check_time_based_alerts():
    now = datetime.now()
    for device in get_all_devices():
        if device.status == "ON":
            if not (OFFICE_START <= now.time() <= OFFICE_END):
                maybe_fire_off_hours_alert(device)

    for room in get_all_rooms():
        devices = get_devices_in_room(room)
        if all(d.status == "ON" for d in devices):
            oldest_on_time = min(d.last_changed for d in devices)
            if now - oldest_on_time >= DURATION_THRESHOLD:
                maybe_fire_room_duration_alert(room)
```

- `OFFICE_START`, `OFFICE_END`, and `DURATION_THRESHOLD` are hardcoded constants (or env vars — see Section 6), **not** magic numbers scattered through the code.
- `maybe_fire_*` functions must de-duplicate — check SQLite for an existing *unresolved* alert of the same type/target before creating a new one, or you'll spam a new alert every 30 seconds forever.

### 4.3 Alert Lifecycle
- **Triggered:** Either path detects a rule breach → alert record created in SQLite → pushed to the Alert Event Stream.
- **Consumed:** Discord bot receives the event, optionally passes it through the LLM for phrasing, posts to the designated channel.
- **Displayed:** Dashboard receives the same event over its WebSocket, renders it in the Active Alerts Panel with a timestamp.
- **Resolved (recommended addition):** When the underlying condition clears (device turns off, or time re-enters 9–5), mark the alert resolved in SQLite so the Active Alerts Panel doesn't accumulate stale entries indefinitely.

---

## 5. Communication Strategy

- **Web Dashboard (no refresh):** FastAPI updates hot state → broadcasts diff via WebSocket → frontend JS updates SVG/DOM (`glow` class on lights, `spin` class on fans) → recalculates Live Power Meter client-side or receives the recalculated total from the server.
- **Discord Bot:**
  - **Commands (`!status`, `!room`, `!usage`):** Bot → **REST** call to FastAPI → response. (v1.1's diagram listed this as "WebSocket/REST," which was inconsistent with the component description — REST alone is correct here since these are pull, not push.)
  - **Proactive alerts:** Bot maintains a persistent WebSocket/SSE connection to the Alert Event Stream, separate from the command path.
  - **Discord Gateway connection:** Standard `discord.py` gateway WebSocket to listen for `!commands`, independent of the above.

---

## 6. Configuration & Demo Mode

A 2-hour threshold is unwatchable in a 3-minute demo video. Thresholds must be config-driven, not hardcoded inline, so they can be shrunk for recording and restored for the "real" system:

```python
# config.py
OFFICE_START = time(9, 0)
OFFICE_END = time(17, 0)
DURATION_THRESHOLD = timedelta(hours=2)   # override via env var for demo, e.g. timedelta(seconds=20)
```

Recommended: read these from environment variables with the production values as defaults, so `DURATION_THRESHOLD_SECONDS=20` can be set only in the demo run without touching source.

---

## 7. Engineering Trade-offs & Validation

| Decision | Trade-off / Rationale |
|---|---|
| Python simulator over Wokwi runtime | Wokwi can't run 3 parallel instances pushing to a remote API reliably; a script gives deterministic demo data while the Wokwi schematic stays a pure hardware-reference deliverable. |
| In-memory hot state (Redis optional) | 18 devices don't need Redis's throughput; an in-memory dict is equally fast and removes a moving part from setup/demo risk. Swap in Redis only if you need persistence across backend restarts. |
| SQLite for cold state | Time-series logging for kWh math and duration tracking without complex data structures; trivial to set up, zero infra. |
| Separate Alert Event Stream from Bot REST API | Keeps the Discord token and posting logic entirely inside the bot service; FastAPI never touches Discord credentials or rate limits. |
| Server-side timestamping | Simulator sends only state changes; FastAPI applies `last_changed`. All time math is anchored to one clock, avoiding skew bugs. |
| Dual-path alerting (event + periodic sweep) | Event-only evaluation cannot detect clock-crossing conditions (off-hours, duration) since no device event necessarily occurs at the threshold moment. The periodic sweep is the fix; the event path stays as a fast-path optimization, not a replacement. |

### Validation Approach
1. Toggle a device in `simulator.py` → confirm the Web Dashboard updates in <1s with no refresh.
2. Run `!status` in Discord → confirm it matches the dashboard exactly.
3. Set `DURATION_THRESHOLD` to 20s and turn on all devices in one room → confirm a Room Duration Alert fires within one sweep interval (~30s), appears in the Active Alerts Panel, and posts to Discord.
4. Override the server clock (or `OFFICE_END`) to simulate 8:30 PM with a device left ON → confirm the Off-Hours Alert fires from the periodic sweep even though no new device event occurred.
5. Confirm alerts de-duplicate — leave the breach condition active for several sweep cycles and verify only one open alert exists per condition/target, not one per tick.

---

## 8. Repository Structure (for grading: "well-structured, documented codebase")

```text
/
├── README.md                 # setup + run instructions for backend, dashboard, bot
├── ARCHITECTURE.md            # this document
├── diagrams/
│   ├── system-diagram.png     # final Excalidraw/draw.io export
│   └── hardware-schematic.png # Wokwi/Tinkercad export
├── backend/
│   ├── main.py                 # FastAPI app, ingestion + WebSocket routes
│   ├── alerts.py                # event-driven + periodic sweep logic
│   ├── config.py                # thresholds, env var loading
│   ├── models.py                # SQLite schema / ORM models
│   └── state.py                 # hot-state store
├── simulator/
│   └── simulator.py
├── dashboard/
│   └── ...                      # frontend
└── bot/
    ├── bot.py                   # discord.py gateway + commands
    └── llm.py                   # Ollama/LLM prompt wrapper
```

The README should cover: prerequisites, environment variables (including the demo-mode threshold override from Section 6), how to start each of the four services, and which port/URL each one listens on.
