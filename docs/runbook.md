# Runbook — Phase 1

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
docker compose logs -f hmi-dashboard
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

## Common issues

- **Port already in use.** Change `PLC_PORT` or `HMI_PORT` in `.env`.
- **HMI shows the error banner immediately.** The simulator container may
  not be healthy yet — `docker compose ps` will show its health status. Wait
  a few seconds and reload.
- **Stale build.** `docker compose build --no-cache <service>` forces a
  clean rebuild.

## Development outside Docker

Simulator:

```bash
cd services/plc-simulator
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

HMI (the Vite dev server proxies `/api` and `/health` to `localhost:8000`):

```bash
cd services/hmi-dashboard
npm install
npm run dev
# then open http://localhost:5173
```
