# Simulator

Standalone Python script that emulates **15 office devices** (2 fans + 3 lights × 3 rooms)
and POSTs `heartbeat` and `state_change` payloads to the FastAPI ingestion gateway.

## Run

From the repo root, with the backend already running:

```powershell
python -m simulator.simulator
```

## Configuration

Copy `simulator/.env.example` to `simulator/.env` and tweak, or export the variables in your shell.

| Variable | Default | Description |
|---|---|---|
| `SIMULATOR_API_URL` | `http://127.0.0.1:8000` | Backend base URL |
| `SIMULATOR_TOGGLE_PROB` | `0.2` | Probability of toggling a device per room tick |
| `SIMULATOR_HEARTBEAT_EVERY_N` | `10` | Send a full-room heartbeat every N ticks |
| `SIMULATOR_SEED` | _(none)_ | Optional integer for deterministic runs |

You can also override on the CLI:

```powershell
python -m simulator.simulator --probability 0.4 --room drawing_room --seed 42
```

## Behavior

- One async loop per room, staggered:
  - Drawing Room → every **3 s**
  - Work Room 1 → every **5 s**
  - Work Room 2 → every **7 s**
- On startup: emits one `heartbeat` per room (all devices `off`).
- Each tick: with `TOGGLE_PROB`, flips one random device in the room and emits `state_change`.
- Every `HEARTBEAT_EVERY_N` ticks per room: emits a full-room `heartbeat` for resync.

## See also

- [`../doc/SIMULATOR.md`](../doc/SIMULATOR.md) — Implementation guide
- [`../doc/SYSTEM_GUIDE.md`](../doc/SYSTEM_GUIDE.md) — How the full system fits together