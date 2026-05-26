import { useCallback, useEffect, useState } from "react";
import { getState, resetSim, setPump } from "./api";
import type { ProcessState } from "./types";
import "./App.css";

const POLL_INTERVAL_MS = 2000;

export default function App() {
  const [state, setState] = useState<ProcessState | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

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
    const id = setInterval(poll, POLL_INTERVAL_MS);

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

  return (
    <div className="app">
      <h1>OT Lab HMI</h1>
      <p className="subtitle">Simulated water-tank process · read &amp; control</p>

      {error && <div className="banner error">{error}</div>}
      {state?.alarm && <div className="banner alarm">ALARM · tank level out of range</div>}

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
      </div>

      <p className="disclaimer">
        Educational simulation only. Not a real industrial control system.
      </p>
    </div>
  );
}
