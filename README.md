# OT Lab-in-a-Box

A fully local, Docker-based simulated operational technology (OT) environment
for learning infrastructure design, process monitoring, and OT/IT segmentation
concepts. The project is **educational and defensive only**.

> This lab is a simulated OT environment for learning infrastructure design,
> monitoring, and segmentation concepts. It does not target real devices and
> should not be connected to production networks. The project is defensive
> and educational only.

## Status

**Phase 5** — safe failure scenarios added. Services are placed on four
named Docker networks (`corp_net`, `dmz_net`, `ot_net`, `monitoring_net`)
modelling a corporate/DMZ/OT/monitoring split, and the lab now includes
deterministic failure demos for high tank alarm, PLC unavailable, HMI
connection loss, historian unavailable, and historian poll errors. A
`corporate-client` container self-tests the segmentation on startup. The
HMI and Grafana are the only host-published services.

The full roadmap (portfolio polish) is tracked in
[`ot_lab_in_a_box_project_plan.md`](ot_lab_in_a_box_project_plan.md).

## What's built

```
                 ┌─────────────────────────────────┐
                 │             Browser             │
                 └────┬───────────────────────┬────┘
                  :3000                     :3001
                      │                       │
  ┌───────────────────┼───────────────────────┼─────────────────────────────────┐
  │                   ▼                       │                                 │
  │  ┌──────────────────────────┐             │                                 │
  │  │     hmi-dashboard        │  dmz_net    │                                 │
  │  │    (nginx + React)       │             │                                 │
  │  └──────────┬───────────────┘             │                                 │
  │             │  /api/*                     │                                 │
  │   - - - - - │ - - - - - - - - - - - - - - │ - - - - - - - - - - - - - - - -│
  │             ▼                             ▼                                 │
  │  ┌──────────────────┐    ┌────────────────────┐         ┌────────────────┐  │
  │  │   plc-simulator  │◀── │     prometheus     │ ───────▶│     grafana    │  │
  │  │     (FastAPI)    │    │   scrapes /metrics │         │  (provisioned) │  │
  │  └────────┬─────────┘    └─────────┬──────────┘         └───────┬────────┘  │
  │           │ poll                   │                            │           │
  │           ▼                        │           monitoring_net   │           │
  │  ┌──────────────────┐              │              ┌─────────────▼─────┐     │
  │  │    historian     │──INSERT──────┼─────────────▶│    postgres       │     │
  │  │   (FastAPI +     │              │              │ process_readings  │     │
  │  │     asyncio)     │              └──── PromQL ──┤  (named volume)   │     │
  │  └──────────────────┘                             └───────────────────┘     │
  │            ot_net                                                           │
  │                                                                             │
  │   - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -│
  │                                                                             │
  │   corp_net:  ┌────────────────────┐                                         │
  │              │  corporate-client  │  (sees nothing else — by design)        │
  │              └────────────────────┘                                         │
  └─────────────────────────────────────────────────────────────────────────────┘
```

Full zone breakdown and traffic rules: [`docs/network-zones.md`](docs/network-zones.md),
[`docs/allowed-traffic-matrix.md`](docs/allowed-traffic-matrix.md).

- **`plc-simulator`** — Python + FastAPI service simulating a water tank
  (level, pump state, inflow/outflow, temperature, alarm). Updates state in
  the background and exposes a JSON API plus `/metrics`.
- **`historian`** — Python + FastAPI worker that polls `plc-simulator` every
  2 seconds and writes each reading to PostgreSQL. Exposes a read-back API
  (`/api/history/readings`) and `/metrics`. Survives simulator and DB
  outages without crashing.
- **`postgres`** — PostgreSQL 16 with the `process_readings` table created
  on first boot via `config/postgres/init.sql`. Data lives in the named
  volume `postgres_data`. Port is intentionally not published.
- **`hmi-dashboard`** — React + TypeScript dashboard, built with Vite and
  served by nginx. Operator-facing UI: pump on/off, reset, live values,
  recent readings.
- **`prometheus`** — Scrapes `/metrics` from the simulator and historian
  every 5 seconds. 7-day retention in the `prometheus_data` volume. Not
  reachable from the host in Phase 5 — query through Grafana → Explore.
  Loads local alerting rules for the safe failure scenarios.
- **`grafana`** — Pre-provisioned dashboard (Prometheus + Postgres
  datasources). Engineer-facing UI for trends and scrape health. Anonymous
  Viewer is enabled for the local lab; admin login still works for editing.
- **`corporate-client`** — Alpine container on `corp_net` only. Runs a
  startup self-test that probes OT/DMZ/monitoring targets — every probe
  is expected to fail, demonstrating that segmentation works.
- **Safe failure scenarios** — documented local-only demos for process
  alarm, PLC outage, HMI connection loss, historian outage, and historian
  poll errors. See [`docs/runbook.md`](docs/runbook.md#safe-failure-scenarios).

### Ports

| Service        | Host port | Purpose                              |
|----------------|-----------|--------------------------------------|
| hmi-dashboard  | 3000      | Operator UI (DMZ)                    |
| grafana        | 3001      | Engineer dashboards (monitoring)     |

`plc-simulator`, `historian`, `prometheus`, `postgres`, and
`corporate-client` are not published to the host. Reach them via
`docker compose exec`, via the HMI's nginx proxy, or via Grafana's
datasources, depending on the zone.

## Quick start

### Prerequisites

- **Docker Engine 24+** and **Docker Compose v2** (`docker compose ...`, not the legacy `docker-compose`).
  - macOS / Windows: [Docker Desktop](https://www.docker.com/products/docker-desktop/) includes both.
  - Linux: install `docker-ce` and the `docker-compose-plugin` package from your distro or Docker's official repo.
- **Git** to clone the repo.
- Free ports on the host: **3000** (HMI) and **3001** (Grafana). Override in `.env` if either is taken.

Verify your setup:

```bash
docker --version
docker compose version
```

### Install and boot

```bash
# 1. Clone
git clone https://github.com/<your-user>/ot-lab-in-a-box.git
cd ot-lab-in-a-box

# 2. Create your local env file (defaults are fine for local use)
cp .env.example .env

# 3. Build images and start all lab services
docker compose up --build
```

First build takes a few minutes (Python, Node, Postgres, and nginx images
download; the React app and Python deps install). Subsequent starts are
fast.

When the logs settle, open:

- **HMI dashboard (operator):** <http://localhost:3000>
- **Grafana (engineer):** <http://localhost:3001> — opens directly into the
  "OT Lab — Overview" dashboard, no login required.
- Simulator API (proxied through HMI): <http://localhost:3000/api/state>
- Simulator health (proxied): <http://localhost:3000/health>
- Persisted readings (proxied): <http://localhost:3000/api/history/readings?limit=5>

Verify segmentation:

```bash
docker compose logs corporate-client
```

Every probe in the log should show `[PASS] ... UNREACHABLE (expected)`.

The "Recent readings" table in the HMI populates within ~10 seconds of
boot, once the historian has polled the simulator a few times.

### Stop and clean up

```bash
# Foreground session: Ctrl+C, then stop containers
docker compose down

# Run in the background instead
docker compose up -d --build
docker compose logs -f          # tail logs
docker compose down             # stop

# Wipe persisted readings too (drops the postgres volume)
docker compose down -v
```

More commands — inspecting Postgres, simulating outages, dev-without-Docker —
are in [`docs/runbook.md`](docs/runbook.md).

## API summary

All endpoints are reachable from the host **only** through the HMI's
nginx on `:3000` (e.g. `http://localhost:3000/api/state`). The simulator
and historian are no longer published directly — that is intentional, see
[`docs/network-zones.md`](docs/network-zones.md).

| Method | Path                          | Served by       | Purpose                               |
|--------|-------------------------------|-----------------|---------------------------------------|
| GET    | `/health`                     | plc-simulator   | Liveness probe                        |
| GET    | `/api/state`                  | plc-simulator   | Current process state (JSON)          |
| POST   | `/api/control/pump`           | plc-simulator   | `{"running": bool}` — toggle the pump |
| POST   | `/api/sim/reset`              | plc-simulator   | Re-initialize the simulation          |
| GET    | `/api/history/readings`       | historian       | Recent persisted readings (newest first). Query params: `limit` (1–1000, default 100), `since` (ISO-8601). |

`/metrics` on both the simulator (`:8000`) and historian (`:8001`) is
scraped by Prometheus inside the compose network. It is not proxied
through the HMI — engineers consume metrics via Grafana.

Example `GET /api/state`:

```json
{
  "tank_level": 61.4,
  "pump_running": true,
  "inflow_rate": 2.0,
  "outflow_rate": 1.2,
  "temperature": 18.9,
  "alarm": false,
  "last_updated": "2026-05-26T12:00:00Z"
}
```

## Documentation

- [`docs/architecture.md`](docs/architecture.md) — service layout per phase.
- [`docs/network-zones.md`](docs/network-zones.md) — the four-zone model.
- [`docs/allowed-traffic-matrix.md`](docs/allowed-traffic-matrix.md) — every allowed and forbidden edge.
- [`docs/runbook.md`](docs/runbook.md) — running, inspecting, troubleshooting.
- [`docs/limitations.md`](docs/limitations.md) — what this lab is and is not.

## Roadmap

Subsequent phase (from the project plan):

1. Portfolio polish.

## Development notes

This project may use AI-assisted development workflows, but repository
authorship and contributor metadata remain under the human project owner.
