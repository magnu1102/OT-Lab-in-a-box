# OT Lab-in-a-Box Project Plan

Single source of truth for planning and developing a public GitHub portfolio project.

## 1. Project summary

**Working name:** OT Lab-in-a-Box  
**Repository name suggestion:** `ot-lab-in-a-box`

OT Lab-in-a-Box is a fully local, Docker-based simulated operational technology environment. It is designed to demonstrate OT/IT segmentation, safe infrastructure design, process monitoring, historian logging, observability, and defensive documentation without connecting to real industrial equipment or real production networks.

The project should be publicly showcaseable on GitHub. It should be educational, defensive, and safe. It must not include exploit code, attack automation, real-world scanning, or instructions that could be used against real OT systems.

The initial simulated process should be simple and understandable: a water tank process with a tank level, pump state, temperature value, and alarm state.

The project should show that the developer understands infrastructure, networking, segmentation, monitoring, service boundaries, and operational documentation.

## 2. Core goal

The goal is to build a miniature OT environment that can be started locally with:

```bash
docker compose up
```

The first complete version should include:

1. A simulated PLC/process service.
2. A simple HMI dashboard.
3. A historian service that stores readings.
4. PostgreSQL for historian data.
5. Prometheus/Grafana or a similar monitoring stack.
6. Multiple Docker networks representing IT, DMZ, OT, and monitoring zones.
7. Clear documentation explaining architecture, allowed flows, limitations, and defensive design choices.

## 3. Portfolio positioning

This project should complement AI and application-development projects by showing a different skill set:

- Docker Compose
- network segmentation concepts
- OT/IT architecture
- DMZ and jump-zone thinking
- service-to-service communication
- monitoring and observability
- PostgreSQL
- Grafana/Prometheus
- defensive documentation
- operational runbooks
- infrastructure reasoning

Suggested portfolio bullet:

```text
Built a Docker-based simulated OT lab with segmented IT/DMZ/OT networks, a Python PLC/process simulator, HMI dashboard, PostgreSQL historian and Prometheus/Grafana monitoring. The project documents allowed traffic flows, failure scenarios and defensive architecture choices.
```

## 4. Safety and scope boundaries

This project must stay defensive and educational.

### Allowed

- Local simulation of OT concepts
- Fake process data
- Docker-based networks
- Defensive monitoring
- Logs and dashboards
- Architecture diagrams
- Safe failure scenarios
- Documentation of segmentation and allowed flows
- Simple service health checks

### Not allowed

- Exploit scripts
- Payloads
- Attack automation
- Real target scanning
- Instructions for compromising PLCs, HMIs or industrial networks
- Code intended to bypass authentication or segmentation
- Use of real industrial system data
- Connecting the lab to production networks
- Claiming that this simulates a production-grade OT environment

Suggested README safety text:

```text
This lab is a simulated OT environment for learning infrastructure design, monitoring and segmentation concepts. It does not target real devices and should not be connected to production networks. The project is defensive and educational only.
```

## 5. AI agent and contribution policy

This project may be planned or implemented with help from AI coding agents, but all agents must follow these rules:

1. **Do not add yourself as a contributor.**
2. **Do not add generated-by footers.**
3. **Do not add “Co-authored-by” lines to commits, files, changelogs or documentation.**
4. **Do not create or edit contributor lists to include AI tools, agents or model names.**
5. **Do not add AI attribution comments to source files.**
6. **Do not add badges or README sections crediting an AI agent.**
7. **Do not modify repository ownership, author metadata or license metadata unless explicitly asked.**
8. **Do not add external service branding unless it is technically required for setup documentation.**
9. **Keep implementation notes technical and project-focused.**

Acceptable phrasing in planning documentation:

```text
This project may use AI-assisted development workflows, but repository authorship and contributor metadata should remain under the human project owner.
```

Unacceptable examples:

```text
Generated with Claude Code
Built by ChatGPT
Co-authored-by: Claude
Contributors: Claude, ChatGPT, Codex
```

## 6. High-level architecture

The lab represents a simplified OT/IT environment:

```text
Corporate IT network
        |
        v
OT DMZ / jump zone
        |
        v
OT control network
        |
        v
Simulated PLC / process device
        |
        v
HMI dashboard and historian
        |
        v
Monitoring stack
```

The first simulated process should be a water tank:

```text
Tank level rises when pump is running.
Tank level slowly falls when pump is off.
Temperature varies slightly over time.
Alarm becomes true if tank level is too high or too low.
```

The simulation does not need to be physically perfect. It only needs to be plausible enough to demonstrate process monitoring and infrastructure behaviour.

## 7. Suggested repository structure

```text
ot-lab-in-a-box/
│
├── README.md
├── docker-compose.yml
├── .env.example
├── LICENSE
│
├── docs/
│   ├── architecture.md
│   ├── network-zones.md
│   ├── allowed-traffic-matrix.md
│   ├── threat-model.md
│   ├── runbook.md
│   ├── failure-scenarios.md
│   └── limitations.md
│
├── diagrams/
│   ├── architecture.mmd
│   └── network-zones.mmd
│
├── services/
│   ├── plc-simulator/
│   │   ├── Dockerfile
│   │   ├── pyproject.toml
│   │   ├── README.md
│   │   └── app/
│   │       ├── main.py
│   │       ├── simulation.py
│   │       ├── models.py
│   │       └── metrics.py
│   │
│   ├── hmi-dashboard/
│   │   ├── Dockerfile
│   │   ├── package.json
│   │   ├── index.html
│   │   └── src/
│   │       ├── App.tsx
│   │       ├── api/
│   │       ├── components/
│   │       └── types/
│   │
│   ├── historian/
│   │   ├── Dockerfile
│   │   ├── pyproject.toml
│   │   └── app/
│   │       ├── main.py
│   │       ├── collector.py
│   │       ├── db.py
│   │       └── models.py
│   │
│   └── corporate-client/
│       ├── Dockerfile
│       └── README.md
│
├── config/
│   ├── prometheus/
│   │   └── prometheus.yml
│   ├── grafana/
│   │   ├── dashboards/
│   │   └── provisioning/
│   └── postgres/
│       └── init.sql
│
├── scripts/
│   ├── reset_lab.sh
│   ├── smoke_test.sh
│   └── generate_sample_events.py
│
└── tests/
    └── README.md
```

The structure can be simplified during Phase 1. Do not overbuild the folder structure before the first services run.

## 8. Services

### 8.1 PLC simulator

**Purpose:** Simulate a physical process device.

Recommended implementation:

- Python
- FastAPI
- simple in-memory simulation loop
- `/state` endpoint for current process state
- `/health` endpoint
- `/metrics` endpoint for Prometheus later

Example state:

```json
{
  "tank_level": 61.4,
  "pump_running": true,
  "temperature": 18.9,
  "alarm": false,
  "timestamp": "2026-05-26T12:00:00Z"
}
```

MVP endpoints:

```text
GET /health
GET /state
GET /metrics later
```

Later endpoints may include safe simulation controls:

```text
POST /simulate/alarm
POST /simulate/reset
POST /simulate/pump-mode
```

Do not implement anything that looks like an exploit or real PLC control interface.

### 8.2 HMI dashboard

**Purpose:** Display process state to an operator.

Recommended implementation:

- React + TypeScript + Vite
- Poll PLC simulator every second or every few seconds
- Display tank level, pump state, temperature, alarm state, connection status and last updated timestamp

MVP UI:

```text
Tank Level: 61.4%
Pump: Running
Temperature: 18.9°C
Alarm: Normal
Last update: 12:00:03
```

Later UI features:

- trend chart
- alarm banner
- connection loss warning
- simulated operator acknowledgement
- read-only mode vs simulated control mode

### 8.3 Historian

**Purpose:** Store process readings over time.

Recommended implementation:

- Python worker
- polls PLC simulator on interval
- writes readings to PostgreSQL
- exposes `/health` endpoint if implemented as FastAPI

MVP table:

```sql
CREATE TABLE process_readings (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL,
    tank_level DOUBLE PRECISION NOT NULL,
    pump_running BOOLEAN NOT NULL,
    temperature DOUBLE PRECISION NOT NULL,
    alarm BOOLEAN NOT NULL
);
```

Later improvements:

- event table for alarms
- retention settings
- query endpoint
- CSV export

### 8.4 PostgreSQL

**Purpose:** Store historian data.

Use standard PostgreSQL container.

MVP:

- database created by init script
- table for process readings
- durable Docker volume

### 8.5 Monitoring stack

**Purpose:** Show operational visibility.

Recommended implementation:

- Prometheus
- Grafana

MVP metrics:

- service health
- tank level
- pump state
- alarm state
- request counts if simple

Grafana dashboard should show:

- tank level over time
- temperature over time
- alarm state
- service uptime or scrape status

### 8.6 Corporate client

**Purpose:** Represent a corporate IT-side service or user workstation.

MVP status:

- Optional in Phase 1.

Later use:

- Demonstrate that direct access to OT services is not intended.
- Run smoke tests from corporate side.
- Document why corporate-to-PLC direct access is not allowed.

Do not build offensive scanning or attack behaviour.

## 9. Network zones

Use Docker Compose networks to represent zones.

Suggested networks:

```text
corp_net
- corporate-side services

dmz_net
- jump/gateway/HMI boundary services

ot_net
- PLC simulator, historian and OT-side services

monitoring_net
- Prometheus, Grafana and metrics access
```

Example service placement:

```text
corporate-client:
  corp_net

jump-host or gateway:
  corp_net, dmz_net

hmi-dashboard:
  dmz_net, ot_net

plc-simulator:
  ot_net

historian:
  ot_net, monitoring_net

prometheus:
  monitoring_net, ot_net

grafana:
  monitoring_net
```

The README should clearly explain that Docker Compose networks are a teaching model, not a replacement for real firewalls, VLANs or industrial security architecture.

## 10. Allowed traffic matrix

A documented traffic matrix is a key deliverable.

Initial table:

| Source | Destination | Purpose | Allowed | Notes |
|---|---|---|---|---|
| HMI dashboard | PLC simulator | Read process state | Yes | HMI needs current state |
| Historian | PLC simulator | Poll readings | Yes | Stores process data |
| Prometheus | PLC simulator | Scrape metrics | Yes | Monitoring only |
| Prometheus | Historian | Scrape metrics | Yes | Monitoring only |
| Grafana | Prometheus | Dashboard queries | Yes | Visualization |
| Corporate client | PLC simulator | Direct OT access | No | Should not bypass DMZ |
| Corporate client | HMI dashboard | Operator view/demo access | Maybe | Only if intentionally exposed |
| HMI dashboard | PostgreSQL | Direct database access | No | HMI should not bypass services |

This table should live in `docs/allowed-traffic-matrix.md`.

## 11. Failure scenarios

The lab should eventually demonstrate operational monitoring, not only happy-path operation.

Suggested safe scenarios:

### Scenario 1: High tank level alarm

- Tank level crosses threshold.
- Alarm state becomes true.
- HMI shows alarm banner.
- Historian stores alarm state.
- Grafana displays alarm period.

### Scenario 2: PLC simulator unavailable

- Stop PLC container.
- HMI shows connection loss.
- Historian logs failed poll.
- Prometheus shows target down.

### Scenario 3: Historian unavailable

- Stop PostgreSQL or historian container.
- HMI still shows current state.
- Monitoring indicates historian failure.
- Documentation explains loss of historical visibility.

### Scenario 4: Flat network comparison

- Conceptual documentation only at first.
- Explain how a flat network creates unnecessary access paths.
- Compare with segmented lab design.

Do not include destructive scenarios.

## 12. Documentation plan

### README.md

Should include:

- project summary
- architecture diagram
- what it demonstrates
- safety notice
- quick start
- services
- network zones
- screenshots
- limitations
- future work

### docs/architecture.md

Should explain:

- service architecture
- data flow
- design choices
- why this is a simulation

### docs/network-zones.md

Should explain:

- corp_net
- dmz_net
- ot_net
- monitoring_net
- service placement
- segmentation assumptions

### docs/allowed-traffic-matrix.md

Should include the traffic matrix.

### docs/threat-model.md

Should stay high-level and defensive.

Suggested sections:

- assets
- trust boundaries
- assumptions
- risks
- defensive controls demonstrated
- what is out of scope

### docs/runbook.md

Should explain:

- start lab
- stop lab
- inspect containers
- check HMI
- check database
- check monitoring
- simulate safe failure scenarios later

### docs/limitations.md

Should explain:

- not production-grade
- Docker networks are simplified
- no real PLCs
- no real industrial protocol initially
- not a substitute for OT security training
- no offensive tooling

## 13. Development phases

### Phase 1: Basic PLC simulator and HMI

Goal:

Create the smallest useful demo: a simulated process service and a dashboard that displays live process state.

Scope:

- Create repository structure
- Add Docker Compose
- Add PLC simulator service
- Add `/health` and `/state`
- Add simple HMI dashboard
- Connect HMI to PLC simulator
- Add basic README quick start

Done when:

- `docker compose up` starts both services
- browser shows changing process values
- README explains how to run the demo

Do not add historian, Prometheus or Grafana in Phase 1 unless the basic flow is already working.

### Phase 2: Historian and PostgreSQL

Goal:

Store process readings over time.

Scope:

- Add PostgreSQL container
- Add historian worker
- Create process_readings table
- Poll PLC simulator and store readings
- Add basic verification instructions

Done when:

- readings are written to PostgreSQL
- user can inspect stored readings

### Phase 3: Monitoring stack

Goal:

Add infrastructure observability.

Scope:

- Add Prometheus
- Add metrics endpoint to PLC simulator
- Add metrics endpoint to historian if useful
- Add Grafana
- Add pre-provisioned dashboard

Done when:

- Grafana shows tank level, temperature and alarm state over time

### Phase 4: Segmentation model and docs

Goal:

Make the infrastructure design visible and defensible.

Scope:

- Add multiple Docker networks
- Place services in intended zones
- Add architecture diagram
- Add network-zones documentation
- Add allowed traffic matrix

Done when:

- repo clearly explains zone model and allowed communication paths

### Phase 5: Failure scenarios

Goal:

Demonstrate operational behaviour under safe failure conditions.

Scope:

- high tank alarm
- PLC unavailable
- historian unavailable
- HMI connection loss
- runbook instructions

Done when:

- user can run documented scenarios and observe effects in HMI/logs/Grafana

### Phase 6: Polish and GitHub presentation

Goal:

Make the project portfolio-ready.

Scope:

- screenshots
- diagrams
- clean README
- limitations
- short demo GIF if desired
- smoke test script
- basic tests
- GitHub Actions if useful

Done when:

- a technical recruiter or interviewer can understand the project quickly
- the lab can be run locally by following the README

## 14. Technical choices

### Recommended for Phase 1

- Docker Compose
- Python + FastAPI for PLC simulator
- React + TypeScript + Vite for HMI dashboard

### Recommended for Phase 2

- PostgreSQL
- Python worker for historian

### Recommended for Phase 3

- Prometheus
- Grafana

### Optional later

- simple Modbus-style register abstraction
- actual Modbus simulator library if safe and clearly documented
- OpenTelemetry
- Zeek/sample logs
- asset inventory view
- alert manager

Avoid adding these too early.

## 15. Environment and configuration

Use `.env.example` for configuration.

Example variables:

```text
PLC_PORT=8000
HMI_PORT=3000
POSTGRES_DB=ot_lab
POSTGRES_USER=ot_lab
POSTGRES_PASSWORD=change_me
HISTORIAN_POLL_INTERVAL_SECONDS=2
```

Do not commit real secrets.

## 16. Initial Phase 1 planning prompt

Use this with a planning agent later:

```text
/plan

We are starting a new public GitHub portfolio project called `ot-lab-in-a-box`.

The goal is to build a safe, fully local, Docker-based simulated OT environment that demonstrates infrastructure design, OT/IT segmentation concepts, process monitoring and defensive documentation. The project must be educational and defensive only. It must not include exploit code, attack automation, real-world scanning or instructions for compromising OT systems.

Important contribution policy:
- Do not add yourself as a contributor.
- Do not add generated-by footers.
- Do not add Co-authored-by lines.
- Do not add AI tools, agents or model names to README, contributors, changelog, package metadata or source comments.
- Keep repository authorship and contributor metadata under the human project owner.

Phase 1 goal:
Build the smallest useful demo: a simulated PLC/process service and an HMI dashboard that displays live process state.

Phase 1 stack:
- Docker Compose
- Python + FastAPI for the PLC simulator
- React + TypeScript + Vite for the HMI dashboard

Phase 1 services:
1. `plc-simulator`
   - Simulates a simple water tank process.
   - Maintains tank level, pump state, temperature and alarm state.
   - Exposes `GET /health`.
   - Exposes `GET /state` returning JSON.
   - Values should change over time.

2. `hmi-dashboard`
   - Simple web UI.
   - Polls the PLC simulator.
   - Shows tank level, pump state, temperature, alarm state and last updated time.
   - Shows a clear connection error if the PLC simulator is unavailable.

Phase 1 repository structure should prepare for future phases but not overbuild:
- `services/plc-simulator/`
- `services/hmi-dashboard/`
- `docs/`
- `diagrams/`
- `docker-compose.yml`
- `.env.example`
- `README.md`

Important design principles:
- Keep the first version small and working end-to-end.
- Prefer simple, readable code over clever abstractions.
- Do not add historian, PostgreSQL, Prometheus or Grafana in Phase 1 unless the basic simulator and HMI are already working.
- Add only minimal documentation needed for running and understanding Phase 1.
- Include a safety notice that this is a simulated defensive lab, not a production OT system.

Please inspect the repository state first, then propose a step-by-step implementation plan for Phase 1. Do not write a large amount of code yet. I want a clear build order, file structure, tradeoffs and any setup decisions before implementation.
```

## 17. Current decision log

- Project selected: OT Lab-in-a-Box.
- The project will be safe, simulated and defensive.
- Initial process simulation: water tank.
- First phase should only build PLC simulator and HMI.
- Historian, monitoring and segmentation docs come after the basic demo works.
- The repository should be public and GitHub-friendly.
- AI agents must not add themselves as contributors or add generated-by attribution.
- Documentation is a core deliverable, not an afterthought.
