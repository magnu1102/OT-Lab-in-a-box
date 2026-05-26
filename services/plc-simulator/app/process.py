"""Water-tank process simulation.

Pure-Python state container with a step function. No I/O — the FastAPI app
drives stepping from an asyncio background task.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from datetime import datetime, timezone


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class WaterTankProcess:
    tank_level: float = 50.0
    pump_running: bool = True
    inflow_rate: float = 2.0
    outflow_rate: float = 1.2
    temperature: float = 18.5
    alarm: bool = False
    last_updated: datetime = field(default_factory=_utcnow)

    HIGH_ALARM: float = 95.0
    LOW_ALARM: float = 5.0
    TEMP_MIN: float = 15.0
    TEMP_MAX: float = 25.0

    def step(self, dt: float) -> None:
        effective_inflow = self.inflow_rate if self.pump_running else 0.0
        self.tank_level = _clamp(
            self.tank_level + (effective_inflow - self.outflow_rate) * dt,
            0.0,
            100.0,
        )
        self.temperature = _clamp(
            self.temperature + random.uniform(-0.05, 0.05) * dt,
            self.TEMP_MIN,
            self.TEMP_MAX,
        )
        self.alarm = self.tank_level < self.LOW_ALARM or self.tank_level > self.HIGH_ALARM
        self.last_updated = _utcnow()

    def set_pump(self, running: bool) -> None:
        self.pump_running = running
        self.last_updated = _utcnow()

    def reset(self) -> None:
        self.tank_level = 50.0
        self.pump_running = True
        self.inflow_rate = 2.0
        self.outflow_rate = 1.2
        self.temperature = 18.5
        self.alarm = False
        self.last_updated = _utcnow()


def _clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))
