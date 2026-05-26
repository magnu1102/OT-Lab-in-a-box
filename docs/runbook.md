# Runbook

## Prerequisites

- Docker Engine 24+
- Docker Compose v2 (`docker compose ...`, not the legacy `docker-compose`)

## Start the lab

```bash
cp .env.example .env       # first time only
docker compose up --build
```

Then open <http://localhost:3000> in a browser.

## Stop the lab

```bash
# Foreground: Ctrl+C, then:
docker compose down

# Background: started with `-d`?
docker compose down
```

## Rebuild after code changes

```bash
docker compose up --build
```

Or rebuild a single service:

```bash
docker compose build plc-simulator
docker compose up -d plc-simulator
```

## Inspect logs

```bash
docker compose logs -f plc-simulator
docker compose logs -f historian
docker compose logs -f postgres
docker compose logs -f hmi-dashboard
docker compose logs -f prometheus
docker compose logs -f grafana
```

## Hit the API from a terminal

```bash
# Health
curl http://localhost:8000/health

# State (repeat — values change)
curl http://localhost:8000/api/state | jq

# Stop the pump (tank level will start trending down)
curl -X POST http://localhost:8000/api/control/pump \
  -H 'Content-Type: application/json' \
  -d '{"running": false}'

# Start it again
curl -X POST http://localhost:8000/api/control/pump \
  -H 'Content-Type: application/json' \
  -d '{"running": true}'

# Reset the simulation
curl -X POST http://localhost:8000/api/sim/reset
```

## Inspect persisted readings

The historian's API is reached via the HMI's nginx (its own port is not
published):

```bash
# Latest 5 readings, newest first
curl 'http://localhost:3000/api/history/readings?limit=5' | jq

# Only readings newer than a given timestamp
curl 'http://localhost:3000/api/history/readings?limit=200&since=2026-05-26T12:00:00Z' | jq
```

Or query Postgres directly:

```bash
# Count rows
docker compose exec postgres \
  psql -U ot_lab -d ot_lab -c 'SELECT count(*) FROM process_readings;'

# Tail the last 10 rows
docker compose exec postgres \
  psql -U ot_lab -d ot_lab -c \
  'SELECT timestamp, tank_level, pump_running, alarm FROM process_readings ORDER BY timestamp DESC LIMIT 10;'

# Interactive shell
docker compose exec postgres psql -U ot_lab -d ot_lab
```

## Back up / wipe the data volume

```bash
# Backup
docker compose exec postgres pg_dump -U ot_lab ot_lab > backup.sql

# Wipe (loses all stored readings)
docker compose down
docker volume rm "$(basename "$PWD" | tr '[:upper:] ' '[:lower:]-')_postgres_data"
```

The volume name is `<project>_postgres_data`, where `<project>` is
docker-compose's slugified project directory name. `docker volume ls` will
show the exact name.

## Use Grafana and Prometheus

- Grafana: <http://localhost:3001> — opens directly into "OT Lab — Overview"
  (anonymous Viewer). To edit panels, sign in with the admin credentials
  from `.env` (default `admin/admin`).
- Prometheus: <http://localhost:9090>. Useful pages:
  - `/targets` — should show both `plc-simulator` and `historian` as `UP`.
  - `/graph` — quick PromQL exploration.

PromQL examples:

```promql
# Live tank level
ot_lab_tank_level_percent

# Scrape health for the OT services
up{job=~"plc-simulator|historian"}

# Historian error rate over 5 minutes
rate(ot_lab_historian_polls_total{result="error"}[5m])

# Histogram p95 of poll duration
histogram_quantile(0.95, sum by (le) (rate(ot_lab_historian_poll_duration_seconds_bucket[5m])))
```

Raw metric scrapes:

```bash
curl http://localhost:8000/metrics | grep ot_lab_
docker compose exec historian curl -s http://localhost:8001/metrics | grep ot_lab_historian_
```

### Editing the provisioned dashboard

The dashboard is `config/grafana/dashboards/ot-lab-overview.json`, mounted
read-only into the container. To iterate:

1. Sign in to Grafana as admin and edit panels in the UI.
2. **Save the dashboard** (`Ctrl+S`) — the change is in Grafana's local DB
   only and will be lost on `docker compose down -v`.
3. Open *Dashboard settings → JSON Model*, copy the JSON, paste it over
   `ot-lab-overview.json`, and commit.

The `dashboards.yml` provider re-reads files every 30 seconds, so the next
`docker compose up` (or `docker compose restart grafana`) will load your
committed version.

## Try the connection-loss banner

In one terminal:

```bash
docker compose stop plc-simulator
```

Within ~2 seconds the HMI dashboard should show a yellow
"Connection to PLC simulator lost" banner. Start it again with:

```bash
docker compose start plc-simulator
```

## Try a historian outage

```bash
docker compose stop historian
```

The live panel keeps updating. The "Recent readings" card shows
"Historian unavailable" within ~5 seconds. No rows are lost — Postgres is
untouched. Restart with `docker compose start historian` and new rows
resume on the next poll tick.

## Common issues

- **Port already in use.** Change `PLC_PORT` or `HMI_PORT` in `.env`.
- **HMI shows the error banner immediately.** The simulator container may
  not be healthy yet — `docker compose ps` will show its health status. Wait
  a few seconds and reload.
- **Stale build.** `docker compose build --no-cache <service>` forces a
  clean rebuild.
- **Historian fails to connect to Postgres on first start.** It retries for
  ~30s; check `docker compose logs historian`. If it eventually gives up,
  Postgres healthcheck logs will explain why.
- **Schema didn't get created.** `init.sql` only runs on **first** init of
  the data volume. If you previously ran an empty Postgres on the same
  volume, wipe the volume (see above) and start again.
- **Grafana panels are empty.** Open <http://localhost:9090/targets> — if
  either job is `DOWN`, the panel will be empty. If targets are `UP`, the
  data may simply be too recent (give it ~30s after first boot).
- **Grafana dashboard shows "Datasource not found".** The provisioning
  files use the literal UIDs `Prometheus` and `Postgres`. If you renamed a
  datasource in the UI, restore the originals or update the dashboard JSON.

## Development outside Docker

Simulator:

```bash
cd services/plc-simulator
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Historian (needs a reachable Postgres and simulator):

```bash
cd services/historian
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
POSTGRES_HOST=localhost POSTGRES_PORT=5432 \
POSTGRES_DB=ot_lab POSTGRES_USER=ot_lab POSTGRES_PASSWORD=change_me \
PLC_SIMULATOR_URL=http://localhost:8000 \
uvicorn app.main:app --reload --port 8001
```

For host-local Postgres, the easiest path is to run only that container:
`docker compose up -d postgres` and then publish the port temporarily by
adding `ports: ["5432:5432"]` to its compose entry **only for the dev
session**.

HMI (the Vite dev server proxies `/api/history` to `localhost:8001` and the
rest of `/api` + `/health` to `localhost:8000`):

```bash
cd services/hmi-dashboard
npm install
npm run dev
# then open http://localhost:5173
```
