"""Prometheus metrics for the PLC simulator."""

from __future__ import annotations

from prometheus_client import Counter, Gauge

from .process import WaterTankProcess

TANK_LEVEL = Gauge(
    "ot_lab_tank_level_percent",
    "Current simulated tank fill level (0-100).",
)
TEMPERATURE = Gauge(
    "ot_lab_temperature_celsius",
    "Current simulated tank temperature.",
)
PUMP_RUNNING = Gauge(
    "ot_lab_pump_running",
    "1 if the simulated pump is running, 0 if stopped.",
)
ALARM = Gauge(
    "ot_lab_alarm",
    "1 if the process alarm is active, 0 otherwise.",
)
INFLOW_RATE = Gauge(
    "ot_lab_inflow_rate_units_per_second",
    "Configured pump inflow rate.",
)
OUTFLOW_RATE = Gauge(
    "ot_lab_outflow_rate_units_per_second",
    "Configured outflow rate.",
)

PUMP_COMMANDS_TOTAL = Counter(
    "ot_lab_pump_commands_total",
    "Pump control commands received.",
    ["result"],
)
SIM_RESETS_TOTAL = Counter(
    "ot_lab_sim_resets_total",
    "Number of times the simulation has been reset.",
)


def update_from_state(process: WaterTankProcess) -> None:
    TANK_LEVEL.set(process.tank_level)
    TEMPERATURE.set(process.temperature)
    PUMP_RUNNING.set(1.0 if process.pump_running else 0.0)
    ALARM.set(1.0 if process.alarm else 0.0)
    INFLOW_RATE.set(process.inflow_rate)
    OUTFLOW_RATE.set(process.outflow_rate)
