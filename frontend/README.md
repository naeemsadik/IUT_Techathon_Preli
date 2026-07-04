# Office Energy Monitor — Frontend (Next.js)

A modern, minimal dashboard for the office energy monitoring system.

| Tech | Why |
|---|---|
| **Next.js 14** (App Router) | SSR, RSC, edge deployment |
| **TypeScript** | type-safe API client |
| **Tailwind CSS** | utility-first styling, dark theme baked in |
| **shadcn-style components** | Card, Button, Badge, Tabs, Table, Skeleton — copy-in, no lock-in |
| **Recharts** | composed, responsive charts |
| **lucide-react** | clean iconography |
| **Zustand** | lightweight global state for live device diffs |
| **Sonner** | toast notifications |

---

## Pages

| Route | Purpose |
|---|---|
| `/`         | Overview — total wattage, KPI cards, 3 rooms, live alerts |
| `/rooms`    | Per-room breakdown with full device grid |
| `/analytics`| Time-series charts: total power, stacked per-room, distribution, top devices, alert timeline. Supports **1H / 24H / 7D / 30D** ranges. |
| `/usage`    | kWh consumption: daily / weekly / monthly + per-room table |
| `/alerts`   | Historical alert table (resolved vs open) + live feed |
| `/devices`  | All 15 devices with search & status/type filters |
| `/settings` | Backend URL + deployment info |

---

## Run locally

```bash
cd frontend
npm install

cp .env.example .env.local
# (defaults to http://127.0.0.1:8000 — should match your local backend)

npm run dev
# → http://localhost:3000
```

---

## Build & production

```bash
npm run build
npm start
```

---

## Environment Variables

| Variable | Description |
|---|---|
| `NEXT_PUBLIC_API_BASE_URL` | Backend base URL. **Required.** Local: `http://127.0.0.1:8000`. Prod: `https://api.yourdomain.com`. |
| `NEXT_PUBLIC_WS_BASE_URL`  | WebSocket base URL — must match the API scheme. Local: `ws://127.0.0.1:8000`. Prod: `wss://api.yourdomain.com`. |

If `NEXT_PUBLIC_WS_BASE_URL` is unset, the client derives it from the API URL
(replacing `http` → `ws`, `https` → `wss`).

---

## Deploy to Vercel

1. Push the repo to GitHub.
2. Sign in to <https://vercel.com> → **Add New Project** → import the repo.
3. **Root Directory:** `frontend`
4. **Framework Preset:** Next.js (auto-detected)
5. **Environment Variables (Production + Preview):**
   - `NEXT_PUBLIC_API_BASE_URL` = `https://api.yourdomain.com`
   - `NEXT_PUBLIC_WS_BASE_URL`  = `wss://api.yourdomain.com`
6. Click **Deploy**.

Every push to `main` redeploys. Every PR gets a preview URL.

### Custom domain

Vercel → Project → **Settings → Domains** → add `office.yourdomain.com`.
Vercel auto-issues the Let's Encrypt cert.

---

## Project Structure

```
frontend/
├── app/
│   ├── layout.tsx          # Root layout (sidebar + topbar)
│   ├── globals.css
│   ├── page.tsx            # Overview
│   ├── rooms/page.tsx
│   ├── analytics/page.tsx  # All charts
│   ├── usage/page.tsx
│   ├── alerts/page.tsx
│   ├── devices/page.tsx
│   └── settings/page.tsx
├── components/
│   ├── ui/                 # shadcn primitives
│   ├── sidebar.tsx
│   ├── top-bar.tsx
│   ├── kpi-card.tsx
│   ├── power-meter.tsx
│   ├── room-card.tsx
│   ├── device-tile.tsx
│   ├── alert-feed.tsx
│   ├── charts.tsx          # All Recharts wrappers
│   ├── range-picker.tsx
│   └── live-store-provider.tsx
└── lib/
    ├── types.ts            # API + UI types
    ├── api.ts              # Typed fetch wrappers
    ├── utils.ts            # cn(), formatters
    └── use-live-store.ts   # Zustand store + WebSocket hooks
```

---

## Adding a new component (shadcn pattern)

```bash
# Just copy a component from https://ui.shadcn.com/docs/components/button
# into components/ui/<name>.tsx, install any deps if needed.
```

We deliberately don't use the shadcn CLI to keep the dependency tree minimal.
All components are designed for **dark theme** and the office-energy look.
