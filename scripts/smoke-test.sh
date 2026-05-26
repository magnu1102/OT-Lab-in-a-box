#!/usr/bin/env bash

set -euo pipefail

HMI_URL="${HMI_URL:-http://localhost:3000}"
GRAFANA_URL="${GRAFANA_URL:-http://localhost:3001}"

fail() {
  echo "[FAIL] $*" >&2
  exit 1
}

pass() {
  echo "[PASS] $*"
}

json_field() {
  local field="$1"
  python3 -c "import json,sys; print(json.load(sys.stdin)${field})"
}

cleanup() {
  curl -fsS -X POST "${HMI_URL}/api/sim/scenario" \
    -H "Content-Type: application/json" \
    -d '{"scenario":"normal"}' >/dev/null || true
}
trap cleanup EXIT

command -v docker >/dev/null || fail "docker is not installed"
command -v curl >/dev/null || fail "curl is not installed"
command -v python3 >/dev/null || fail "python3 is not installed"

docker compose config --quiet
pass "docker compose config is valid"

hmi_code="$(curl -fsS -o /dev/null -w "%{http_code}" "${HMI_URL}/")"
[[ "$hmi_code" == "200" ]] || fail "HMI returned HTTP ${hmi_code}"
pass "HMI is reachable"

state_json="$(curl -fsS "${HMI_URL}/api/state")"
tank_level="$(printf '%s' "$state_json" | json_field "['tank_level']")"
pump_running="$(printf '%s' "$state_json" | json_field "['pump_running']")"
[[ "$tank_level" =~ ^[0-9]+([.][0-9]+)?$ ]] || fail "tank_level is not numeric: ${tank_level}"
[[ "$pump_running" == "True" || "$pump_running" == "False" ]] || fail "pump_running is not boolean"
pass "process state endpoint returns JSON"

scenario_json="$(curl -fsS -X POST "${HMI_URL}/api/sim/scenario" \
  -H "Content-Type: application/json" \
  -d '{"scenario":"high_tank"}')"
alarm="$(printf '%s' "$scenario_json" | json_field "['alarm']")"
[[ "$alarm" == "True" ]] || fail "high_tank scenario did not activate alarm"
pass "high_tank scenario activates alarm"

normal_json="$(curl -fsS -X POST "${HMI_URL}/api/sim/scenario" \
  -H "Content-Type: application/json" \
  -d '{"scenario":"normal"}')"
alarm="$(printf '%s' "$normal_json" | json_field "['alarm']")"
[[ "$alarm" == "False" ]] || fail "normal scenario did not clear alarm"
pass "normal scenario clears alarm"

readings_json="$(curl -fsS "${HMI_URL}/api/history/readings?limit=1")"
reading_count="$(printf '%s' "$readings_json" | python3 -c "import json,sys; print(len(json.load(sys.stdin)))")"
[[ "$reading_count" -ge 1 ]] || fail "historian returned no readings"
pass "historian returns persisted readings"

rules_json="$(docker compose exec -T grafana \
  wget -qO- "http://prometheus:9090/api/v1/rules")"
for alert in OTProcessAlarm PLCSimulatorDown HistorianDown HistorianPollErrors; do
  if ! printf '%s' "$rules_json" | python3 -c "import json,sys; data=json.load(sys.stdin); names=[r.get('name') for g in data['data']['groups'] for r in g.get('rules', [])]; sys.exit(0 if '$alert' in names else 1)"; then
    fail "Prometheus alert rule missing: ${alert}"
  fi
done
pass "Prometheus exposes Phase 5 alert rules"

corp_logs="$(docker compose logs --no-color corporate-client)"
pass_count="$(printf '%s' "$corp_logs" | grep -c "\\[PASS\\].*UNREACHABLE" || true)"
fail_count="$(printf '%s' "$corp_logs" | grep -c "\\[FAIL\\]" || true)"
[[ "$pass_count" -ge 6 ]] || fail "corporate-client did not report all segmentation passes"
[[ "$fail_count" -eq 0 ]] || fail "corporate-client reported a segmentation failure"
pass "corporate-client segmentation self-test passed"

grafana_code="$(curl -fsS -o /dev/null -w "%{http_code}" "${GRAFANA_URL}/")"
[[ "$grafana_code" == "200" || "$grafana_code" == "302" ]] || fail "Grafana returned HTTP ${grafana_code}"
pass "Grafana is reachable"

echo
echo "Smoke test passed. Simulator reset to normal."
