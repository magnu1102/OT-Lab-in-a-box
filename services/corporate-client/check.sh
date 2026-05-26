#!/usr/bin/env bash
# Defensive segmentation self-test for the OT Lab-in-a-Box.
#
# This container sits on corp_net only. It tries to reach OT, DMZ, and
# monitoring services by their container names. EVERY probe is EXPECTED
# TO FAIL — that is the entire point of the zone model. A failure means
# segmentation is working; success means the zone model has leaked.
#
# This is not an attack tool. It probes a fixed list of declared local
# targets, expects them to be unreachable, and reports the result.

set -u

banner() {
  echo "================================================================"
  echo " corporate-client segmentation self-test"
  echo " I live on corp_net only. Every probe below should be"
  echo " UNREACHABLE. Any REACHABLE result is a zone-model leak."
  echo "================================================================"
}

probe_http() {
  local label="$1"
  local url="$2"
  local code
  code="$(curl --max-time 3 -s -o /dev/null -w '%{http_code}' "$url" 2>/dev/null || true)"
  if [[ -z "$code" || "$code" == "000" ]]; then
    echo "  [PASS] $label -> UNREACHABLE (expected)   $url"
  else
    echo "  [FAIL] $label -> REACHABLE (HTTP $code)   $url"
  fi
}

probe_tcp() {
  local label="$1"
  local host="$2"
  local port="$3"
  # Alpine's curl supports telnet:// for a raw TCP test without netcat.
  if curl --max-time 3 -s "telnet://${host}:${port}" </dev/null >/dev/null 2>&1; then
    echo "  [FAIL] $label -> REACHABLE              ${host}:${port}"
  else
    echo "  [PASS] $label -> UNREACHABLE (expected)  ${host}:${port}"
  fi
}

banner
echo
echo "Probing forbidden cross-zone targets..."
probe_http "hmi-dashboard (DMZ)"   "http://hmi-dashboard/api/state"
probe_http "plc-simulator (OT)"    "http://plc-simulator:8000/api/state"
probe_http "historian (OT/mon)"    "http://historian:8001/api/history/readings?limit=1"
probe_http "prometheus (OT/mon)"   "http://prometheus:9090/-/healthy"
probe_http "grafana (monitoring)"  "http://grafana:3000/api/health"
probe_tcp  "postgres (monitoring)" "postgres" "5432"
echo
echo "Self-test complete. Container will stay up for manual inspection."
echo "Try:  docker compose exec corporate-client sh"
echo

exec sleep infinity
