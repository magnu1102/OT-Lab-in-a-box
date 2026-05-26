# Architecture

The lab is built incrementally. Phase 1 introduced the live simulator and
HMI; Phase 2 adds persistence. Network segmentation and monitoring come in
later phases.

## Current components (Phases 1 + 2)

```
                    ┌─────────────────────────────────┐
                    │            Browser              │
                    └────────────────┬────────────────┘
                                     │ HTTP :3000
                                     ▼
        ┌──────────────────────────────────────────────────────┐
        │                  hmi-dashboard                        │
        │              (nginx + React/TypeScript)               │
        │  /api/state, /api/control/* ─▶ plc-simulator:8000     │
        │  /api/history/*           ─▶ historian:8001           │
        └────────────────┬───────────────────────┬──────────────┘
                         │                       │
                         ▼                       ▼
              ┌──────────────────┐    ┌─────────────────────┐
              │  plc-simulator   │◀───│      historian      │
              │    (FastAPI)     │poll│ (FastAPI + asyncio) │
              │     :8000        │    │        :8001        │
              └──────────────────┘    └──────────┬──────────┘
                                                 │ psycopg
                                                 ▼
                                       ┌────────────────────┐
                                       │      postgres      │
                                       │ process_readings   │
                                       │   (named volume)   │
                                       └────────────────────┘
```

### `plc-simulator` (Phase 1)

- Python 3.12, FastAPI, Uvicorn.
- `WaterTankProcess` dataclass holds in-memory state. An asyncio background
  task calls `process.step(dt)` every `SIM_TICK_SECONDS` (default 0.5s).
- Endpoints: `GET /health`, `GET /api/state`, `POST /api/control/pump`,
  `POST /api/sim/reset`.
- State is in-memory only — restarting the container resets the tank.
  Persistence is handled by the historian.

### `hmi-dashboard` (Phase 1, extended in Phase 2)

- React 18 + TypeScript, built with Vite. Production image is multi-stage:
  Node builds static assets, nginx serves them and proxies API traffic to
  the backend services by container name.
- nginx routes (longest-prefix wins): `/api/history/*` → `historian:8001`,
  `/api/*` → `plc-simulator:8000`, `/health` → `plc-simulator:8000`,
  everything else → static SPA.
- Polls `/api/state` every 2s and `/api/history/readings?limit=20` every 5s.
- Tolerates either backend being unavailable — the live panel and the
  "Recent readings" table degrade independently.

### `historian` (Phase 2)

- Python 3.12, FastAPI, Uvicorn, psycopg 3 (sync, pooled), httpx (async).
- On startup: opens a psycopg `ConnectionPool` (with retry — Postgres can
  take a moment even when its healthcheck has reported ready).
- A single asyncio task runs `collector.poll_loop`: every
  `HISTORIAN_POLL_INTERVAL_SECONDS` (default 2s), `GET plc-simulator:8000
  /api/state` and `INSERT` into `process_readings`. Poll errors are logged
  and swallowed so the loop survives simulator or DB outages.
- Endpoints: `GET /health` (checks DB), `GET /api/history/readings`
  (read-only). No write endpoints.

### `postgres` (Phase 2)

- `postgres:16-alpine`.
- Schema seeded from `config/postgres/init.sql` via the official image's
  `/docker-entrypoint-initdb.d/` mechanism (runs once, on first init of the
  data volume).
- Data persists in the named volume `postgres_data`.

### Persisted fields

`inflow_rate` and `outflow_rate` are simulator configuration, not measured
process values, so they are intentionally **not** persisted. The
`process_readings` table matches the schema in project plan §8.3:

```sql
id SERIAL PRIMARY KEY,
timestamp TIMESTAMPTZ,
tank_level DOUBLE PRECISION,
pump_running BOOLEAN,
temperature DOUBLE PRECISION,
alarm BOOLEAN
```

## Deliberate non-exposures

- **Postgres port (`5432`) is not published.** Inspection happens via
  `docker compose exec postgres psql ...`. Publishing it would add host
  attack surface for no operational benefit at this scope.
- **Historian port (`8001`) is not published.** Reach it via the HMI's
  nginx (`/api/history/...` on `:3000`) or `docker compose exec historian
  curl localhost:8001/...`. This mirrors how a historian in a real OT
  environment would not be directly internet-facing.
- The **simulator port (`8000`) is** published, for convenience in
  testing and to keep the Phase 1 quick-start unchanged. In Phase 4
  (network zones) it will move behind the DMZ.

## Data flow

1. Simulator background task steps the process every 0.5s.
2. Historian polls `/api/state` every 2s, parses, INSERTs.
3. HMI polls live state every 2s and historian every 5s, renders both.
4. Operator clicks toggle the pump via `POST /api/control/pump`; the next
   simulator poll reflects it, and the next historian poll persists it.

## What changes in later phases

- **Phase 3**: simulator and historian expose `/metrics`; Prometheus scrapes;
  Grafana dashboards visualize trends from Postgres and Prometheus.
- **Phase 4**: services are placed on dedicated Docker networks
  (`corp_net`, `dmz_net`, `ot_net`, `monitoring_net`); direct host
  exposure of `plc-simulator` is removed.
- **Phase 5**: documented failure scenarios (high-level alarm, simulator
  unavailable, historian unavailable) with expected HMI / log / dashboard
  behaviour.
