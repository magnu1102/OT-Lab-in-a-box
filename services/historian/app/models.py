from datetime import datetime

from pydantic import BaseModel


class Reading(BaseModel):
    id: int
    timestamp: datetime
    tank_level: float
    pump_running: bool
    temperature: float
    alarm: bool


class ProcessStatePayload(BaseModel):
    """Subset of plc-simulator /api/state we persist. Extra fields ignored."""

    tank_level: float
    pump_running: bool
    temperature: float
    alarm: bool
    last_updated: datetime


class HealthResponse(BaseModel):
    status: str = "ok"
