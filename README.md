# OT Lab-in-a-Box

A fully local, Docker-based simulated operational technology (OT) environment
for learning infrastructure design, process monitoring, and OT/IT segmentation
concepts. The project is **educational and defensive only**.

> This lab is a simulated OT environment for learning infrastructure design,
> monitoring, and segmentation concepts. It does not target real devices and
> should not be connected to production networks. The project is defensive
> and educational only.

## Status

**Phase 2** — persistence layer added. Readings from the simulator are now
polled and stored in PostgreSQL by a `historian` service, and the HMI shows
the most recent rows.

The full roadmap (Prometheus/Grafana, network zone segmentation, threat
model, failure scenarios) is tracked in
[`ot_lab_in_a_box_project_plan.md`](ot_lab_in_a_box_project_plan.md).

## What's built

```
┌─────────┐    ┌──────────────────┐    ┌────────────────┐    ┌────────────┐
│ Browser │───▶│  hmi-dashboard   │───▶│ plc-simulator  │◀───│ historian  │
│         │    │ (nginx + React)  │    │  (FastAPI)     │    │ (FastAPI,  │
└─────────┘    │       :3000      │    │      :8000     │    │   poll)    │
               └────────┬─────────┘    └────────────────┘    └─────┬──────┘
                        │  /api/history/*                          │
                        └──────────────────────────────────────────┤
                                                                   ▼
                                                          ┌────────────────┐
                                                          │   postgres     │
                                                          │ (process_readings)
                                                          └────────────────┘
```

- **`plc-simulator`** — Python + FastAPI service simulating a water tank
  (level, pump state, inflow/outflow, temperature, alarm). Updates state in
  the background and exposes a JSON API.
- **`historian`** — Python + FastAPI worker that polls `plc-simulator` every
  2 seconds and writes each reading to PostgreSQL. Exposes a read-back API
  (`/api/history/readings`). Survives simulator and DB outages without
  crashing.
- **`postgres`** — PostgreSQL 16 with the `process_readings` table created
  on first boot via `config/postgres/init.sql`. Data lives in the named
  volume `postgres_data`. Port is intentionally not published.
- **`hmi-dashboard`** — React + TypeScript dashboard, built with Vite and
  served by nginx. Polls the simulator every 2 seconds, polls the historian
  every 5 seconds for recent readings, and supports pump on/off and reset.

## Quick start

Requires Docker and Docker Compose.

```bash
cp .env.example .env
docker compose up --build
```

Then open:

- HMI dashboard: <http://localhost:3000>
- Simulator API:  <http://localhost:8000/api/state>
- Simulator health: <http://localhost:8000/health>

Stop with `Ctrl+C` and clean up with `docker compose down`.

## API summary

All endpoints below are reachable through the HMI's nginx on `:3000`
(e.g. `http://localhost:3000/api/state`). The simulator is also published
directly on `:8000` for convenience.

| Method | Path                          | Served by       | Purpose                               |
|--------|-------------------------------|-----------------|---------------------------------------|
| GET    | `/health`                     | plc-simulator   | Liveness probe                        |
| GET    | `/api/state`                  | plc-simulator   | Current process state (JSON)          |
| POST   | `/api/control/pump`           | plc-simulator   | `{"running": bool}` — toggle the pump |
| POST   | `/api/sim/reset`              | plc-simulator   | Re-initialize the simulation          |
| GET    | `/api/history/readings`       | historian       | Recent persisted readings (newest first). Query params: `limit` (1–1000, default 100), `since` (ISO-8601). |

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

- [`docs/architecture.md`](docs/architecture.md) — Phase 1 service layout.
- [`docs/runbook.md`](docs/runbook.md) — running, inspecting, troubleshooting.
- [`docs/limitations.md`](docs/limitations.md) — what this lab is and is not.

## Roadmap

Subsequent phases (from the project plan):

1. Prometheus + Grafana monitoring.
2. Multiple Docker networks for IT/DMZ/OT/monitoring zones, allowed-traffic
   matrix, architecture diagrams.
3. Safe failure scenarios (high-level alarm, simulator unavailable, historian
   unavailable).
4. Portfolio polish.

## Development notes

This project may use AI-assisted development workflows, but repository
authorship and contributor metadata remain under the human project owner.
