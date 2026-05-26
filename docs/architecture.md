# Architecture — Phase 1

Phase 1 is intentionally the smallest end-to-end slice of the full lab. There
is one process simulator and one operator dashboard, on a single Docker
network. Network segmentation, monitoring, and persistence come in later
phases.

## Components

```
┌───────────┐      HTTP       ┌──────────────────┐      HTTP      ┌─────────────────┐
│  Browser  │ ───────────────▶│  hmi-dashboard   │ ──────────────▶│  plc-simulator  │
│           │                 │ (nginx + React)  │                │   (FastAPI)     │
└───────────┘                 └──────────────────┘                └─────────────────┘
                                    :3000                                :8000
                              proxies /api/* and /health to plc-simulator:8000
```

### `plc-simulator`

- Python 3.12, FastAPI, Uvicorn.
- A `WaterTankProcess` dataclass holds in-memory state. An asyncio background
  task calls `process.step(dt)` every `SIM_TICK_SECONDS` (default 0.5s).
- Endpoints: `GET /health`, `GET /api/state`, `POST /api/control/pump`,
  `POST /api/sim/reset`.
- State is **in-memory only** — restarting the container resets the tank.

### `hmi-dashboard`

- React 18 + TypeScript, built with Vite.
- Production image is multi-stage: Node builds static assets, nginx serves
  them and proxies `/api/*` and `/health` to the simulator container by name
  (`plc-simulator:8000`).
- The browser only talks to one origin (the nginx container), which sidesteps
  CORS and mirrors how a real HMI fronts a control-network service.

## Data flow

1. Background task in the simulator steps the process every 0.5s, updating
   tank level, temperature, and alarm state.
2. The HMI polls `GET /api/state` every 2 seconds.
3. Operator clicks toggle the pump via `POST /api/control/pump`; the next
   poll reflects the new state.

## Why a simulation

The goal is to demonstrate OT/IT infrastructure thinking (service
boundaries, segmentation, monitoring, runbooks) in a safe, fully local
environment. The simulator does **not** speak any industrial protocol and is
not a substitute for working with real PLCs or HMIs.

## What changes in later phases

- **Phase 2**: a historian service polls `/api/state` and writes readings to
  PostgreSQL.
- **Phase 3**: simulator exposes `/metrics`; Prometheus scrapes; Grafana
  dashboards visualize trends.
- **Phase 4**: services are placed on dedicated Docker networks
  (`corp_net`, `dmz_net`, `ot_net`, `monitoring_net`) to model segmentation,
  and direct access to the simulator from outside the OT zone is removed.
