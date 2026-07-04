# Deployment Guide - Coolify Backend + Vercel Frontend

This project deploys as two public pieces:

| Component | Where | How |
|---|---|---|
| IUT server (FastAPI + SQLite) | Contabo VPS via Coolify | Root `docker-compose.yaml` |
| Frontend (Next.js) | Vercel | Git integration with root directory `frontend` |
| Simulator | Local or VPS optional process | `python -m simulator.simulator` |
| Discord bot | Local or VPS optional process | `python -m bot.bot` |

The old static `dashboard/` app has been removed. The frontend lives in
`frontend/` and talks to the backend over REST plus WebSockets.

---

## 1. Backend on Coolify

### 1.1 Push the repo to GitHub

Coolify builds from a Git repository.

```powershell
git init
git remote add origin https://github.com/naeemsadik/IUT_Techathon_Preli.git
git add .
git commit -m "Initial commit with deployment configs"
git push -u origin main
```

### 1.2 Create the Coolify resource

In Coolify:

1. Add a new resource from your Git repository.
2. Choose the Docker Compose deployment option.
3. Set the compose file path to `docker-compose.yaml`.
4. Select the `iut_server` service.
5. Assign your API domain to the `iut_server` service on container port `8000`.
6. Set the health check path to `/api/health`.

The `iut_server/Dockerfile` can stay in the repository because Compose uses it to
build the image. The deployment entry point in Coolify is the root
`docker-compose.yaml`, not a Dockerfile resource.

### 1.3 Environment variables

`docker-compose.yaml` defines defaults for the backend. In Coolify, set at
least:

```env
CORS_ALLOW_ORIGINS=https://your-vercel-app.vercel.app
```

Recommended production values:

```env
DEBUG=false
OFFICE_START=09:00
OFFICE_END=17:00
DURATION_THRESHOLD_SECONDS=7200
DEVICE_DURATION_THRESHOLD_SECONDS=3600
ALERT_SWEEP_INTERVAL_SECONDS=30
CORS_ALLOW_ORIGINS=https://your-vercel-app.vercel.app,https://office.yourdomain.com
```

Do not include trailing slashes in CORS origins.

### 1.4 SQLite persistence

The compose file mounts a named volume:

```yaml
office-energy-data:/app/data
```

The SQLite database path inside the container is:

```text
/app/data/office_energy.db
```

Keep this volume attached across redeploys or history will be lost.

### 1.5 Smoke test

After Coolify deploys and your domain points to the resource:

```bash
curl https://api.yourdomain.com/api/health
curl "https://api.yourdomain.com/api/history?range=24h"
```

---

## 2. Frontend on Vercel

### 2.1 Project settings

In Vercel:

1. Import the same GitHub repository.
2. Set Root Directory to `frontend`.
3. Keep Framework Preset as Next.js.
4. Use `npm install` or Vercel's default install command.
5. Use `next build` or Vercel's default build command.
6. Keep Output Directory as `.next`.

The checked-in `frontend/vercel.json` declares the Next.js framework, build
command, install command, output directory, and security headers.

### 2.2 Environment variables

Set these for Production and Preview:

| Name | Value |
|---|---|
| `NEXT_PUBLIC_API_BASE_URL` | `https://api.yourdomain.com` |
| `NEXT_PUBLIC_WS_BASE_URL` | `wss://api.yourdomain.com` |

For local development the frontend defaults to `http://127.0.0.1:8000` and
derives the WebSocket URL automatically.

### 2.3 Build locally before pushing

```powershell
cd frontend
npm ci
npm run build
```

The GitHub Actions workflow also runs this build on pushes and pull requests.

---

## 3. CI/CD

The workflow at `.github/workflows/ci.yml` runs two jobs:

| Job | What it checks |
|---|---|
| Backend tests | Python 3.12, `pip install -r requirements.txt`, `pytest` |
| Frontend build | Node 20, `npm ci`, `npm run build` inside `frontend/` |

Vercel will handle frontend deployment from Git after you connect the project.
Coolify deployment can be connected later by enabling Git auto-deploy or a
Coolify webhook on the same repository. Until Coolify is ready, CI still gives
you a reliable build gate.

---

## 4. Backend on Render

If deploying the backend as a native Python web service on Render, use:

```text
Build Command: pip install -r requirements.txt
Start Command: uvicorn iut_server.app.main:app --host 0.0.0.0 --port $PORT
```

Use these Render environment variables:

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
CORS_ALLOW_ORIGINS=https://iut-techathon-preli.vercel.app

# Run the demo generator inside this same Render web service.
ENABLE_SIMULATOR=true
SIMULATOR_API_URL=https://iut-techathon-preli.onrender.com
SIMULATOR_TOGGLE_PROB=0.6
SIMULATOR_HEARTBEAT_EVERY_N=10

# Optional: run the Discord bot inside this same Render web service.
ENABLE_DISCORD_BOT=false
API_BASE_URL=https://iut-techathon-preli.onrender.com
DISCORD_TOKEN=
ALERT_CHANNEL_ID=
COMMAND_PREFIX=!
LLM_ENABLED=false
GROQ_API_KEY=
GROQ_MODEL=llama-3.3-70b-versatile
```

Do not use `/app/data/office_energy.db` on a native Render Python service. That
path is for the Docker image, and Render's native runtime cannot create `/app`.

For persistent SQLite history on Render, add a Render disk and mount it at:

```text
/var/data
```

Then change the Render env to:

```env
SQLITE_PATH=/var/data/office_energy.db
```

Without a disk, `data/office_energy.db` works, but history can be lost after
redeploys or restarts.

### 4.1 Embedded simulator and bot on Render

For a one-service demo, the FastAPI process can also start the simulator and
Discord bot as background tasks.

Turn on the simulator:

```env
ENABLE_SIMULATOR=true
SIMULATOR_API_URL=https://iut-techathon-preli.onrender.com
SIMULATOR_TOGGLE_PROB=0.6
```

Turn on the bot only after adding your Discord credentials:

```env
ENABLE_DISCORD_BOT=true
API_BASE_URL=https://iut-techathon-preli.onrender.com
DISCORD_TOKEN=your-discord-bot-token
ALERT_CHANNEL_ID=your-alert-channel-id
COMMAND_PREFIX=!
LLM_ENABLED=false
```

If `ENABLE_DISCORD_BOT=true` but `DISCORD_TOKEN` is empty, the server keeps
running and logs that the bot was disabled.

---

## 5. Port 8000 and Coolify

Using container port `8000` is fine. Coolify runs its platform and proxy outside
your application container, then routes traffic from your domain to the service's
container port.

A conflict only happens if you publish a host port with a Compose mapping such
as:

```yaml
ports:
  - "8000:8000"
```

That asks Docker to bind port `8000` on the VPS itself. The root
`docker-compose.yaml` avoids that by using:

```yaml
expose:
  - "8000"
```

So Coolify/Traefik handles public HTTP(S), and the app only listens internally
on port `8000`.

---

## 6. Public verification

1. Open the Vercel frontend.
2. Confirm the overview page loads without CORS errors.
3. POST a state change to the backend:

   ```bash
   curl -X POST https://api.yourdomain.com/api/ingest \
     -H "Content-Type: application/json" \
     -d '{"message_type":"state_change","source_id":"smoke","sequence":1,"device_timestamp":"2026-07-04T14:00:30Z","changes":[{"device_id":"drawing_room_fan_1","room":"drawing_room","device_type":"fan","status":"on","power_draw_w":60}]}'
   ```

4. The frontend should update Drawing Room Fan 1 to ON.
5. Open `/analytics` and confirm `/api/history` returns data.

---

## 7. Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| Frontend shows `Failed to fetch` | Backend CORS does not include the Vercel domain | Update `CORS_ALLOW_ORIGINS` in Coolify |
| WebSocket reconnects forever | WS URL uses `ws://` in production | Set `NEXT_PUBLIC_WS_BASE_URL=wss://api.yourdomain.com` |
| IUT server returns 502 | Container crashed or health check failed | Check Coolify logs for the `iut_server` service |
| History disappears after redeploy | Missing persistent volume | Keep `office-energy-data` mounted to `/app/data` |
| Render startup fails with `Permission denied: '/app'` | Render native runtime is using Docker SQLite path | Set `SQLITE_PATH=data/office_energy.db` or mount a disk and use `/var/data/office_energy.db` |
| Docker says host port already in use | Compose published `8000:8000` | Remove `ports` and use `expose` plus a Coolify domain |

---

## 8. Related Documents

- [`DEMO.md`](./DEMO.md) - Local demo walk-through
- [`SYSTEM_GUIDE.md`](./SYSTEM_GUIDE.md) - System reference
- [`ARCHITECTURE.md`](./ARCHITECTURE.md) - Architecture and trade-offs
