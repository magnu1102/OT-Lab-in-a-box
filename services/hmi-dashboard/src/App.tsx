import { useCallback, useEffect, useState } from "react";
import { getReadings, getState, resetSim, setPump, setScenario } from "./api";
import type { ProcessState, Reading, ScenarioName } from "./types";
import "./App.css";

const STATE_POLL_MS = 2000;
const READINGS_POLL_MS = 5000;
const READINGS_LIMIT = 20;

export default function App() {
  const [state, setState] = useState<ProcessState | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const [readings, setReadings] = useState<Reading[]>([]);
  const [readingsError, setReadingsError] = useState<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    let cancelled = false;

    const poll = async () => {
      try {
        const next = await getState(controller.signal);
        if (!cancelled) {
          setState(next);
          setError(null);
        }
      } catch (err) {
        if (!cancelled && (err as Error).name !== "AbortError") {
          setError("Connection to PLC simulator lost.");
        }
      }
    };

    poll();
    const id = setInterval(poll, STATE_POLL_MS);

    return () => {
      cancelled = true;
      controller.abort();
      clearInterval(id);
    };
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    let cancelled = false;

    const poll = async () => {
      try {
        const next = await getReadings(READINGS_LIMIT, controller.signal);
        if (!cancelled) {
          setReadings(next);
          setReadingsError(null);
        }
      } catch (err) {
        if (!cancelled && (err as Error).name !== "AbortError") {
          setReadingsError("Historian unavailable.");
        }
      }
    };

    poll();
    const id = setInterval(poll, READINGS_POLL_MS);

    return () => {
      cancelled = true;
      controller.abort();
      clearInterval(id);
    };
  }, []);

  const onTogglePump = useCallback(async () => {
    if (!state) return;
    setBusy(true);
    try {
      const next = await setPump(!state.pump_running);
      setState(next);
      setError(null);
    } catch {
      setError("Failed to send pump command.");
    } finally {
      setBusy(false);
    }
  }, [state]);

  const onReset = useCallback(async () => {
    setBusy(true);
    try {
      const next = await resetSim();
      setState(next);
      setError(null);
    } catch {
      setError("Failed to reset simulation.");
    } finally {
      setBusy(false);
    }
  }, []);

  const onScenario = useCallback(async (scenario: ScenarioName) => {
    setBusy(true);
    try {
      const next = await setScenario(scenario);
      setState(next);
      setError(null);
    } catch {
      setError("Failed to apply simulator scenario.");
    } finally {
      setBusy(false);
    }
  }, []);

  const alarmText = state?.alarm
    ? state.tank_level > 95
      ? "ALARM · high tank level"
      : state.tank_level < 5
        ? "ALARM · low tank level"
        : "ALARM · tank level out of range"
    : null;

  return (
    <div className="app">
      <h1>OT Lab HMI</h1>
      <p className="subtitle">Simulated water-tank process · read &amp; control</p>

      {error && <div className="banner error">{error}</div>}
      {alarmText && <div className="banner alarm">{alarmText}</div>}

      <div className="card">
        <div className="row">
          <span className="label">Tank level</span>
          <span className="value">{state ? `${state.tank_level.toFixed(1)} %` : "—"}</span>
        </div>
        <div className={`bar${state?.alarm ? " alarm" : ""}`}>
          <div className="fill" style={{ width: `${state ? state.tank_level : 0}%` }} />
        </div>

        <div className="row">
          <span className="label">Pump</span>
          <span className="value">
            {state ? (state.pump_running ? "Running" : "Stopped") : "—"}
          </span>
        </div>
        <div className="row">
          <span className="label">Inflow rate</span>
          <span className="value">{state ? `${state.inflow_rate.toFixed(2)} u/s` : "—"}</span>
        </div>
        <div className="row">
          <span className="label">Outflow rate</span>
          <span className="value">{state ? `${state.outflow_rate.toFixed(2)} u/s` : "—"}</span>
        </div>
        <div className="row">
          <span className="label">Temperature</span>
          <span className="value">{state ? `${state.temperature.toFixed(1)} °C` : "—"}</span>
        </div>
        <div className="row">
          <span className="label">Alarm</span>
          <span className="value">{state ? (state.alarm ? "Active" : "Normal") : "—"}</span>
        </div>
        <div className="row">
          <span className="label">Last updated</span>
          <span className="value">
            {state ? new Date(state.last_updated).toLocaleTimeString() : "—"}
          </span>
        </div>
      </div>

      <div className="card controls">
        <button
          className="primary"
          onClick={onTogglePump}
          disabled={busy || !state}
        >
          {state?.pump_running ? "Stop pump" : "Start pump"}
        </button>
        <button className="warn" onClick={onReset} disabled={busy}>
          Reset simulation
        </button>
        <div className="scenario-controls" aria-label="Simulator scenarios">
          <button onClick={() => onScenario("high_tank")} disabled={busy || !state}>
            High tank scenario
          </button>
          <button onClick={() => onScenario("normal")} disabled={busy}>
            Normal scenario
          </button>
        </div>
      </div>

      <section className="card readings">
        <header className="readings-header">
          <h2>Recent readings</h2>
          <span className="readings-note">
            {readingsError ?? `last ${readings.length} · from historian`}
          </span>
        </header>
        {readings.length === 0 && !readingsError ? (
          <p className="empty">No readings yet — waiting for historian…</p>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Time</th>
                <th>Level</th>
                <th>Pump</th>
                <th>Temp</th>
                <th>Alarm</th>
              </tr>
            </thead>
            <tbody>
              {readings.map((r) => (
                <tr key={r.id} className={r.alarm ? "alarm" : undefined}>
                  <td>{new Date(r.timestamp).toLocaleTimeString()}</td>
                  <td>{r.tank_level.toFixed(1)} %</td>
                  <td>{r.pump_running ? "on" : "off"}</td>
                  <td>{r.temperature.toFixed(1)} °C</td>
                  <td>{r.alarm ? "✓" : "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>

      <p className="disclaimer">
        Educational simulation only. Not a real industrial control system.
      </p>
    </div>
  );
}
