# Limitations

This project is a **teaching simulation**, not a production-grade OT system.
Be honest about what it is and is not.

## What this project is

- A local Docker-based environment for learning OT/IT infrastructure design.
- A safe sandbox for exploring service boundaries, monitoring, and
  documentation practices.
- A portfolio artifact demonstrating familiarity with Docker Compose,
  Python/FastAPI, React, and operational thinking.

## What this project is not

- **Not a real PLC or HMI.** It does not implement Modbus, OPC UA, EtherNet/IP,
  or any other industrial protocol. The "PLC simulator" is a Python process
  with a JSON API.
- **Not a substitute for OT security training** or hands-on experience with
  real industrial systems.
- **Not production-grade.** There is no authentication, no TLS, no rate
  limiting, no audit logging. Persisted data is stored in plaintext in a
  local Docker volume.
- **Not a security testing tool.** The repository contains no exploit code,
  no attack automation, no scanning utilities, and no instructions for
  compromising real OT systems. It must not be used against real devices.

## Current limitations (Phases 1-5)

- **Simulator state is still in-memory.** Restarting `plc-simulator` resets
  the tank. The historian persists *readings* over time, but the live
  process state itself is not durable.
- **No retention policy.** `process_readings` grows unbounded. At the
  default 2s poll interval that is ~43k rows/day, which is fine for a local
  educational lab but is not a production retention strategy.
- **No authentication or authorization.** Anyone with access to the host's
  exposed ports can call `/api/control/pump`. The historian API has no
  auth either; it is only reachable on the internal Docker network and via
  the HMI nginx proxy. This is acceptable for a local educational lab.
- **Default Postgres password (`change_me`).** Fine for a local lab; would
  obviously need to change for anything else. The host port for Postgres is
  intentionally not published.
- **Anonymous Grafana access is intentional for the local lab.** Anyone
  who can reach `:3001` can view all dashboards without authentication.
  This is convenient for a teaching demo and would be unacceptable on any
  network-exposed deployment. Editing still requires the admin password.
- **`/metrics` endpoints are unauthenticated.** Fine on the internal
  Docker network; do not expose them on a real network.
- **Alerting is local and unrouted.** Prometheus loads rule files for the
  safe failure scenarios, but there is no Alertmanager, paging, email, or
  external notification path. Alerts are inspected through Grafana or
  Prometheus APIs from inside the monitoring zone.
- **Segmentation, not enforcement.** Phase 4 places services on four
  named Docker networks so that non-members cannot resolve or route to
  each other. Containers that **share** a network still have full mutual
  access on any port — Docker networks do not enforce per-port allow-lists,
  rate limits, or deep packet inspection. Real OT environments add
  firewalls, host-based controls, and (sometimes) service meshes. See
  [`docs/network-zones.md`](network-zones.md#what-docker-networks-enforce--and-dont)
  for the full discussion.
- **corporate-client smoke script is defensive.** It probes a fixed list
  of declared local targets, *expecting failure*, and reports the result.
  It performs no exploitation, no port-range scans, and no enumeration
  beyond declared targets. It will not run against anything outside this
  compose project.
- **Failure scenarios are simulated controls.** The high-tank scenario is
  an in-memory simulator shortcut for demos. Docker stop/start scenarios
  model service unavailability only inside this local lab.

## Out of scope, permanently

- Code intended to bypass authentication, segmentation, or other controls.
- Use of real industrial system data.
- Connecting the lab to production networks.
- Claiming that this simulates a production-grade OT environment.
