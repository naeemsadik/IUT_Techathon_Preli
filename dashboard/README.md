# Dashboard

Vanilla HTML/CSS/JS frontend that visualises the live office energy state.

- Initial render via `GET /api/status`
- Live updates via WebSocket `WS /ws/dashboard` (state diffs after each ingest)
- Live alerts via WebSocket `WS /ws/alerts`
- Usage stats via `GET /api/usage` (refreshed every 30s)

## Run

The dashboard is a static page — open it directly, or serve it with any static
HTTP server.

### Option A — Open the file directly

Open `dashboard/index.html` in your browser.

> Note: most browsers block WebSocket connections from `file://` to `ws://localhost`,
> so prefer Option B for a smooth experience.

### Option B — Serve over HTTP

From the repo root:

```powershell
python -m http.server 5500 --directory dashboard
```

Then visit <http://127.0.0.1:5500>.

### Backend URL

By default the dashboard talks to `http://127.0.0.1:8000`. Override at load time
with a query string:

```
http://127.0.0.1:5500/?api=http://192.168.1.20:8000
```

## What you see

- **Total office load** — total wattage, with a horizontal meter (max 345 W).
- **3 room cards** — Drawing Room, Work Room 1, Work Room 2.
  - Each shows 5 devices: **2 fans** + **3 lights**.
  - **Fan** spins (CSS animation) when ON.
  - **Light** glows when ON.
- **Live alerts** — incoming messages from `/ws/alerts`.
- **Energy usage** — daily / weekly / monthly kWh plus per-room totals.

## See also

- [`../doc/SYSTEM_GUIDE.md`](../doc/SYSTEM_GUIDE.md) §2.1 — Ingestion flow that drives the dashboard
- [`../doc/HIGH_LEVEL_DIAGRAMS.md`](../doc/HIGH_LEVEL_DIAGRAMS.md) — Phase 3 system diagrams