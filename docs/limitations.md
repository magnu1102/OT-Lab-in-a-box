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
- **Not production-grade.** State is in-memory; there is no authentication, no
  TLS, no rate limiting, no audit logging.
- **Not a security testing tool.** The repository contains no exploit code,
  no attack automation, no scanning utilities, and no instructions for
  compromising real OT systems. It must not be used against real devices.

## Phase 1 specific

- **No persistence.** Restarting `plc-simulator` resets the tank to its
  initial state. Persistence arrives with the historian (Phase 2).
- **No network segmentation.** Both services share a single default Docker
  network. The DMZ / OT / monitoring zone model is introduced in Phase 4.
- **No authentication or authorization.** Anyone with access to the host's
  exposed ports can call `/api/control/pump`. This is acceptable for a local
  educational lab and is called out in the architecture docs.
- **No monitoring or metrics endpoint.** Phase 3 adds Prometheus-compatible
  `/metrics` and Grafana dashboards.
- **Docker networks are not a security boundary.** When zones are added in
  Phase 4, they will model segmentation conceptually — they are not a
  replacement for real firewalls, VLANs, or industrial security architecture.

## Out of scope, permanently

- Code intended to bypass authentication, segmentation, or other controls.
- Use of real industrial system data.
- Connecting the lab to production networks.
- Claiming that this simulates a production-grade OT environment.
