# OT Lab-in-a-Box

A fully local, Docker-based simulated operational technology (OT) environment
for learning infrastructure design, process monitoring, and OT/IT segmentation
concepts. The project is **educational and defensive only**.

> This lab is a simulated OT environment for learning infrastructure design,
> monitoring, and segmentation concepts. It does not target real devices and
> should not be connected to production networks. The project is defensive
> and educational only.

## Status

**Phase 1** — basic simulated water-tank process and a minimal HMI dashboard.

The full roadmap (historian, PostgreSQL, Prometheus/Grafana, network zone
segmentation, threat model, failure scenarios) is tracked in
[`ot_lab_in_a_box_project_plan.md`](ot_lab_in_a_box_project_plan.md).

## What Phase 1 builds

```
┌───────────┐      HTTP       ┌──────────────────┐      HTTP      ┌─────────────────┐
│  Browser  │ ───────────────▶│  hmi-dashboard   │ ──────────────▶│  plc-simulator  │
│           │                 │ (nginx + React)  │                │   (FastAPI)     │
└───────────┘                 └──────────────────┘                └─────────────────┘
                                    :3000                                :8000
```

- **`plc-simulator`** — Python + FastAPI service simulating a water tank
  (level, pump state, inflow/outflow, temperature, alarm). Updates state in
  the background and exposes a JSON API.
- **`hmi-dashboard`** — React + TypeScript dashboard, built with Vite and
  served by nginx. Polls the simulator every 2 seconds, displays live values,
  and supports a pump on/off control.

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

| Method | Path                  | Purpose                                  |
|--------|-----------------------|------------------------------------------|
| GET    | `/health`             | Liveness probe                           |
| GET    | `/api/state`          | Current process state (JSON)             |
| POST   | `/api/control/pump`   | `{"running": bool}` — toggle the pump    |
| POST   | `/api/sim/reset`      | Re-initialize the simulation             |

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

1. Historian + PostgreSQL.
2. Prometheus + Grafana monitoring.
3. Multiple Docker networks for IT/DMZ/OT/monitoring zones, allowed-traffic
   matrix, architecture diagrams.
4. Safe failure scenarios (high-level alarm, simulator unavailable, historian
   unavailable).
5. Portfolio polish.

## Development notes

This project may use AI-assisted development workflows, but repository
authorship and contributor metadata remain under the human project owner.
