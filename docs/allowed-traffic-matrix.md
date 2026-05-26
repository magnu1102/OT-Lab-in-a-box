# Allowed traffic matrix

Every edge in the design is listed below. Rows marked **No** describe
flows that would violate the zone model — they are listed explicitly so
that the matrix doubles as a regression test: if any of those ever become
reachable, the segmentation has broken.

The "Implemented by" column documents how each rule is realised. In Phase
4, that is **always** Docker network membership. There is no firewall,
service mesh, or policy engine in this lab.

## Allowed flows

| Source           | Destination     | Purpose                                | Allowed | Implemented by                       |
|------------------|-----------------|----------------------------------------|:-------:|--------------------------------------|
| Browser (host)   | hmi-dashboard   | Operator UI                            |   Yes   | Published port `3000` → `hmi:80`     |
| Browser (host)   | grafana         | Engineer dashboards                    |   Yes   | Published port `3001` → `grafana:3000` |
| hmi-dashboard    | plc-simulator   | `/api/state`, `/api/control/pump`      |   Yes   | Shared `ot_net`                      |
| hmi-dashboard    | historian       | `/api/history/readings`                |   Yes   | Shared `ot_net` (historian multi-home) |
| historian        | plc-simulator   | Poll `/api/state`                      |   Yes   | Shared `ot_net`                      |
| historian        | postgres        | INSERT into `process_readings`         |   Yes   | Shared `monitoring_net`              |
| prometheus       | plc-simulator   | Scrape `/metrics`                      |   Yes   | Shared `ot_net`                      |
| prometheus       | historian       | Scrape `/metrics`                      |   Yes   | Shared `ot_net`                      |
| grafana          | prometheus      | PromQL queries                         |   Yes   | Shared `monitoring_net`              |
| grafana          | postgres        | SQL queries (Postgres datasource)      |   Yes   | Shared `monitoring_net`              |

## Forbidden flows (would be a zone violation)

| Source            | Destination     | Why it would be wrong                                                  | Allowed | Implemented by                                  |
|-------------------|-----------------|------------------------------------------------------------------------|:-------:|-------------------------------------------------|
| corporate-client  | hmi-dashboard   | Corp must not reach DMZ-published services directly inside compose     |   No    | `corp_net` has no DMZ peers                     |
| corporate-client  | plc-simulator   | Corp must never reach OT directly — the classic anti-pattern          |   No    | `corp_net` has no OT peers                      |
| corporate-client  | historian       | Same as above                                                          |   No    | `corp_net` has no OT or monitoring peers        |
| corporate-client  | postgres        | Corp must not reach internal data stores                               |   No    | `corp_net` has no monitoring peers              |
| corporate-client  | prometheus      | Corp must not query OT metrics directly                                |   No    | `corp_net` has no OT or monitoring peers        |
| corporate-client  | grafana         | Corp should reach engineer dashboards only through documented portal   |   No    | `corp_net` has no monitoring peers              |
| hmi-dashboard     | postgres        | HMI must not bypass historian to read raw history                      |   No    | HMI is not on `monitoring_net`                  |
| hmi-dashboard     | prometheus      | HMI must not query metrics — that is Grafana's job                     |   No    | HMI is not on `monitoring_net`                  |
| hmi-dashboard     | grafana         | Operator UI must not depend on engineer UI                             |   No    | HMI is not on `monitoring_net`                  |
| grafana           | plc-simulator   | Engineer dashboards must observe via Prometheus, not poll OT directly  |   No    | Grafana is not on `ot_net`                      |
| grafana           | historian       | Same as above                                                          |   No    | Grafana is not on `ot_net`                      |
| plc-simulator     | anything else   | The OT device is a read/write endpoint, not an initiator               |   No    | `plc-simulator` is on `ot_net` only             |
| postgres          | anything else   | A database is only an endpoint, not an initiator                       |   No    | `postgres` is on `monitoring_net` only          |

## Verifying the matrix

The `corporate-client` container's startup script (see [`runbook.md`](runbook.md#demonstrate-the-zone-model))
attempts every probe in the "Forbidden flows" table that is reachable
from `corp_net`. Every probe should fail. Additional spot-checks for the
other forbidden rows are listed in the runbook under the same section.

## Honest caveat

Docker networks **hide** services from non-members but do not restrict
which ports a co-member may access. This matrix represents intent that is
partially enforced by the topology. The unenforced parts — for example,
the fact that `hmi-dashboard` could in principle reach any TCP port on
`plc-simulator` — would be the responsibility of host firewalls, service
meshes, or industrial protocol gateways in a real environment. See
[`network-zones.md`](network-zones.md#what-docker-networks-enforce--and-dont)
for the full discussion.
