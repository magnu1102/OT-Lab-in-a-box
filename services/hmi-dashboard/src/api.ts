import type { ProcessState, Reading, ScenarioName } from "./types";

export async function getState(signal?: AbortSignal): Promise<ProcessState> {
  const res = await fetch("/api/state", { signal });
  if (!res.ok) {
    throw new Error(`GET /api/state failed: ${res.status}`);
  }
  return (await res.json()) as ProcessState;
}

export async function setPump(running: boolean): Promise<ProcessState> {
  const res = await fetch("/api/control/pump", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ running }),
  });
  if (!res.ok) {
    throw new Error(`POST /api/control/pump failed: ${res.status}`);
  }
  const body = (await res.json()) as { accepted: boolean; state: ProcessState };
  return body.state;
}

export async function resetSim(): Promise<ProcessState> {
  const res = await fetch("/api/sim/reset", { method: "POST" });
  if (!res.ok) {
    throw new Error(`POST /api/sim/reset failed: ${res.status}`);
  }
  return (await res.json()) as ProcessState;
}

export async function setScenario(scenario: ScenarioName): Promise<ProcessState> {
  const res = await fetch("/api/sim/scenario", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ scenario }),
  });
  if (!res.ok) {
    throw new Error(`POST /api/sim/scenario failed: ${res.status}`);
  }
  return (await res.json()) as ProcessState;
}

export async function getReadings(
  limit = 20,
  signal?: AbortSignal,
): Promise<Reading[]> {
  const res = await fetch(`/api/history/readings?limit=${limit}`, { signal });
  if (!res.ok) {
    throw new Error(`GET /api/history/readings failed: ${res.status}`);
  }
  return (await res.json()) as Reading[];
}
