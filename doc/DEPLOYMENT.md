# Deployment Guide — Contabo VPS via Coolify + Vercel

This document describes how to deploy the office energy monitoring system
publicly:

| Component | Where | How |
|---|---|---|
| **Backend** (FastAPI + SQLite) | Contabo VPS via Coolify | Docker (multi-stage) |
| **Frontend** (Next.js) | Vercel | Direct git integration |
| **Simulator** | Same VPS (optional) | Docker side-container or systemd |
| **Discord bot** | Same VPS (optional) | Docker side-container or systemd |

```
┌──────────────────┐         ┌────────────────────────────────────────┐
│  Vercel (CDN)    │  HTTPS  │   Contabo VPS (Coolify)                │
│                  │ ──────► │   ┌──────────────────────────────┐    │
│  Next.js app     │         │   │ office-energy-backend        │    │
│  /dashboard      │ ◄────── │   │ FastAPI on :8000             │    │
│  /analytics      │   WS    │   │ SQLite at /app/data/*.db     │    │
└──────────────────┘         │   └──────────────────────────────┘    │
                             │            ▲                            │
                             │            │ POST /api/ingest           │
                             │   ┌────────┴──────────┐                 │
                             │   │ simulator.py      │ (optional)      │
                             │   └───────────────────┘                 │
                             └────────────────────────────────────────┘
```

---

## 1. Backend on Contabo + Coolify

### 1.1 Provision the VPS

1. Buy a Contabo VPS (4 GB RAM / 4 vCPU is plenty for this workload).
2. Install Coolify on it. Coolify auto-installs Docker, Traefik (reverse proxy),
   and a management UI on a public port.
   - See <https://coolify.io/docs/installation>.

### 1.2 Push the repo to GitHub

Coolify builds from a Git repository.

```powershell
git init
git remote add origin https://github.com/<your-username>/IUT_Techathon_Preli.git
git add .
git commit -m "Initial commit with deployment configs"
git push -u origin main
```

### 1.3 Create the resource in Coolify

1. **Add Resource → Application → Public/Private Repository** → paste the
   repo URL.
2. **Build Pack:** Dockerfile
3. **Dockerfile Location:** `backend/Dockerfile`
4. **Port:** `8000`
5. **Healthcheck Path:** `/api/health`

### 1.4 Persistent volume (CRITICAL for SQLite)

The SQLite file lives at `/app/data/office_energy.db` inside the container.
Without a persistent volume, **every redeploy wipes your history**.

In Coolify:

1. Open the resource → **Storages** tab.
2. Add a volume: `/app/data`
3. Coolify will create and attach a Docker volume automatically.

### 1.5 Environment variables

Set these in Coolify's **Environment Variables** editor for the resource:

```env
HOST=0.0.0.0
PORT=8000
DEBUG=false
OFFICE_START=09:00
OFFICE_END=17:00
DURATION_THRESHOLD_SECONDS=7200
DEVICE_DURATION_THRESHOLD_SECONDS=3600
ALERT_SWEEP_INTERVAL_SECONDS=30
SQLITE_PATH=/app/data/office_energy.db

# Replace with your actual Vercel domain once deployed.
CORS_ALLOW_ORIGINS=https://office-energy.vercel.app
```

### 1.6 Domain + TLS

1. In Coolify resource → **Domains** → add `api.yourdomain.com`.
2. Coolify (via Traefik) auto-issues a Let's Encrypt certificate.
3. Backend is now reachable at `https://api.yourdomain.com`.

### 1.7 Smoke test

```bash
curl https://api.yourdomain.com/api/health
# → {"success":true,"data":{"status":"ok",...}}

curl "https://api.yourdomain.com/api/history?range=24h"
# → {"success":true,"data":{"range":"24h",...}}
```

---

## 2. Frontend on Vercel

### 2.1 One-time Vercel setup

1. Sign in to <https://vercel.com>.
2. **Add New Project** → Import the same GitHub repository.
3. **Root Directory:** `frontend` (we'll create this in step 3 below).
4. **Framework Preset:** Next.js (auto-detected).
5. **Build Command:** `next build` (default)
6. **Output Directory:** `.next` (default)

### 2.2 Environment variables

In Vercel project → **Settings → Environment Variables**:

| Name | Value | Scope |
|---|---|---|
| `NEXT_PUBLIC_API_BASE_URL` | `https://api.yourdomain.com` | Production, Preview |
| `NEXT_PUBLIC_WS_BASE_URL` | `wss://api.yourdomain.com` | Production, Preview |

(For local dev, the values default to `http://127.0.0.1:8000`.)

### 2.3 Deploy

Vercel auto-deploys on every push to `main`. Preview deployments are created
for pull requests.

### 2.4 Custom domain (optional)

Vercel project → **Settings → Domains** → add `office.yourdomain.com`.
Vercel auto-issues the certificate.

---

## 3. Discord bot + simulator (optional side-containers)

The Discord bot and simulator are designed to run alongside the backend.
Either:

- Run them on the same VPS as separate **Coolify applications** (one Dockerfile
  each — see `bot/Dockerfile` if added later), or
- Run them with a single `docker-compose.yml` in Coolify's
  **Docker Compose** resource type.

For a techathon demo, the simplest path is just to run them on your laptop
and point them at the public backend URL.

---

## 4. Verifying the public deployment

1. Open `https://office-energy.vercel.app` in a browser.
2. The dashboard should show all 15 devices (mostly OFF at first).
3. POST a test state change:
   ```bash
   curl -X POST https://api.yourdomain.com/api/ingest \
     -H "Content-Type: application/json" \
     -d '{"message_type":"state_change","source_id":"smoke","sequence":1,"device_timestamp":"2026-07-04T14:00:30Z","changes":[{"device_id":"drawing_room_fan_1","room":"drawing_room","device_type":"fan","status":"on","power_draw_w":60}]}'
   ```
4. The dashboard should immediately show Drawing Room Fan 1 ON.
5. Reload the page or switch tabs (e.g. /analytics) — history should be
   populated from `/api/history`.

---

## 5. Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| Frontend loads but `Failed to fetch` everywhere | CORS misconfigured | Update `CORS_ALLOW_ORIGINS` on backend to include your Vercel domain (no trailing slash). |
| History empty after restart | Forgot persistent volume | Add `/app/data` volume in Coolify. |
| `502 Bad Gateway` on backend | Healthcheck failing or app crashed | `docker logs <container>` (or Coolify Logs tab). |
| Vercel build fails on `pnpm`/`npm` lockfile | Repo root has multiple lockfiles | Vercel uses the one inside `frontend/`. If missing, run `cd frontend && npm install` locally once. |
| WebSocket keeps reconnecting | Mixed content / wrong scheme | Ensure `NEXT_PUBLIC_WS_BASE_URL` starts with `wss://` in production. |
| SQLite `readonly database` | Volume mounted read-only | Check Coolify storage settings. |

---

## 6. Related Documents

- [`DEMO.md`](./DEMO.md) — Local demo walk-through
- [`SYSTEM_GUIDE.md`](./SYSTEM_GUIDE.md) — System reference
- [`ARCHITECTURE.md`](./ARCHITECTURE.md) — Architecture & trade-offs