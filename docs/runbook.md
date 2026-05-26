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

In Phase 4, the simulator and historian are no longer published on the
host. All terminal access goes through the HMI's nginx proxy on `:3000`
(or, for engineer-only access, via `docker compose exec`).

```bash
# Health (proxied)
curl http://localhost:3000/health

# State — repeat, values change
curl http://localhost:3000/api/state | jq

# Stop the pump (tank level will start trending down)
curl -X POST http://localhost:3000/api/control/pump \
  -H 'Content-Type: application/json' \
  -d '{"running": false}'

# Start it again
curl -X POST http://localhost:3000/api/control/pump \
  -H 'Content-Type: application/json' \
  -d '{"running": true}'

# Reset the simulation
curl -X POST http://localhost:3000/api/sim/reset
```

To talk to the simulator directly (e.g. to confirm a Phase 4 segmentation
property), exec into a container that lives on `ot_net`:

```bash
docker compose exec plc-simulator curl -s localhost:8000/api/state | jq
docker compose exec hmi-dashboard wget -qO- http://plc-simulator:8000/api/state
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
- Prometheus is **not published to the host** in Phase 4. Run PromQL via
  Grafana → Explore (default datasource is Prometheus) or exec into a
  monitoring-zone container:
  - `docker compose exec grafana wget -qO- http://prometheus:9090/api/v1/targets`
  - `docker compose exec grafana wget -qO- 'http://prometheus:9090/api/v1/query?query=up'`

PromQL examples (paste into Grafana → Explore):

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

Raw metric scrapes from inside the OT/monitoring zone:

```bash
docker compose exec plc-simulator curl -s localhost:8000/metrics | grep ot_lab_
docker compose exec historian curl -s localhost:8001/metrics | grep ot_lab_historian_
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

## Demonstrate the zone model

The `corporate-client` container sits on `corp_net` alone. On startup it
probes every forbidden cross-zone target it can name. Every probe is
expected to fail.

```bash
docker compose logs corporate-client
```

Expected: each line ends with `[PASS] ... UNREACHABLE (expected)`. A
`[FAIL] ... REACHABLE` line means the zone configuration has leaked.

Run more probes interactively:

```bash
docker compose exec corporate-client bash

# From inside the container — all should fail:
curl --max-time 3 -v http://plc-simulator:8000/api/state
curl --max-time 3 -v http://postgres:5432
getent hosts hmi-dashboard      # name resolution should also fail
```

For the positive side of the matrix, exec into a container that *is*
allowed to reach the target and confirm it works:

```bash
docker compose exec hmi-dashboard wget -qO- http://plc-simulator:8000/api/state
docker compose exec grafana      wget -qO- http://prometheus:9090/-/healthy
docker compose exec historian    curl -s http://plc-simulator:8000/api/state | head -c 200
```

Full table of expected results: [`docs/allowed-traffic-matrix.md`](allowed-traffic-matrix.md).

## Try the connection-loss banner

This is part of the safe failure scenario set. It demonstrates what an
operator sees when the HMI can no longer reach the simulated PLC.

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

This is part of the safe failure scenario set. It demonstrates that the
live process view and history panel fail independently.

```bash
docker compose stop historian
```

The live panel keeps updating. The "Recent readings" card shows
"Historian unavailable" within ~5 seconds. No rows are lost — Postgres is
untouched. Restart with `docker compose start historian` and new rows
resume on the next poll tick.

## Safe failure scenarios

All scenarios are local, simulated and defensive. They affect only this
Docker Compose lab.

### High tank alarm

Trigger a deterministic high-level process alarm:

```bash
curl -X POST http://localhost:3000/api/sim/scenario \
  -H 'Content-Type: application/json' \
  -d '{"scenario": "high_tank"}' | jq
```

Expected HMI behavior:

- The alarm banner reads `ALARM · high tank level`.
- Tank level is above 95%.
- Pump state is running so the simulated alarm remains observable.
- Recent historian readings begin showing alarmed rows after the next poll.

Expected Grafana / Prometheus signal:

- `ot_lab_alarm` becomes `1`.
- `ot_lab_tank_level_percent` is above 95.
- Alert rule `OTProcessAlarm` becomes pending, then firing after its `for`
  duration.

Recover:

```bash
curl -X POST http://localhost:3000/api/sim/scenario \
  -H 'Content-Type: application/json' \
  -d '{"scenario": "normal"}' | jq
```

### PLC unavailable / HMI connection loss

Stop the simulator:

```bash
docker compose stop plc-simulator
```

Expected HMI behavior:

- Within one state poll, the HMI shows `Connection to PLC simulator lost.`
- The most recent displayed process values remain visible until recovery.
- The historian may remain reachable, but new rows stop because it cannot
  poll the simulator.

Expected logs / Grafana / Prometheus signal:

- `docker compose logs historian` shows poll failures.
- `up{job="plc-simulator"}` becomes `0`.
- `rate(ot_lab_historian_polls_total{result="error"}[2m])` rises.
- Alert rules `PLCSimulatorDown` and `HistorianPollErrors` become pending,
  then firing after their `for` durations.

Recover:

```bash
docker compose start plc-simulator
```

### Historian unavailable

Stop only the historian:

```bash
docker compose stop historian
```

Expected HMI behavior:

- Live tank values keep updating.
- The history panel shows `Historian unavailable.` within about 5 seconds.

Expected Grafana / Prometheus signal:

- `up{job="historian"}` becomes `0`.
- Alert rule `HistorianDown` becomes pending, then firing after its `for`
  duration.
- Postgres remains running and existing rows remain available.

Recover:

```bash
docker compose start historian
```

### Historian poll errors while service stays up

Stop the simulator while leaving the historian running:

```bash
docker compose stop plc-simulator
docker compose logs -f historian
```

Expected behavior:

- Historian logs repeated poll failures but the container keeps running.
- `ot_lab_historian_polls_total{result="error"}` increments.
- Alert rule `HistorianPollErrors` becomes pending, then firing after its
  `for` duration.

Recover:

```bash
docker compose start plc-simulator
```

## Common issues

- **Port already in use.** Change `HMI_PORT` or `GRAFANA_PORT` in `.env`.
  The simulator and Prometheus no longer publish to the host in Phase 4.
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
- **Grafana panels are empty.** Open Grafana → Explore and run
  `up{job=~"plc-simulator|historian"}` — both should be `1`. If either is
  `0`, the corresponding service is down. If both are `1`, the data may
  simply be too recent (give it ~30s after first boot).
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

Dev-without-Docker requires temporarily publishing the simulator and
Postgres host ports (they are deliberately unpublished in the Phase 4
compose). The simplest path is to add temporary `ports:` overrides to a
local `docker-compose.override.yml` — `git status` will flag it so you
don't commit it.

```yaml
# docker-compose.override.yml  (DO NOT COMMIT)
services:
  plc-simulator:
    ports: ["8000:8000"]
  postgres:
    ports: ["5432:5432"]
```

Then:

```bash
cd services/historian
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
POSTGRES_HOST=localhost POSTGRES_PORT=5432 \
POSTGRES_DB=ot_lab POSTGRES_USER=ot_lab POSTGRES_PASSWORD=change_me \
PLC_SIMULATOR_URL=http://localhost:8000 \
uvicorn app.main:app --reload --port 8001
```

HMI (the Vite dev server proxies `/api/history` to `localhost:8001` and the
rest of `/api` + `/health` to `localhost:8000`):

```bash
cd services/hmi-dashboard
npm install
npm run dev
# then open http://localhost:5173
```
