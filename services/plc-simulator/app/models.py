from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class ProcessState(BaseModel):
    tank_level: float = Field(..., description="Tank fill level in percent (0-100).")
    pump_running: bool
    inflow_rate: float = Field(..., description="Configured inflow rate in units/sec.")
    outflow_rate: float = Field(..., description="Outflow rate in units/sec.")
    temperature: float = Field(..., description="Tank temperature in Celsius.")
    alarm: bool
    last_updated: datetime


class HealthResponse(BaseModel):
    status: str = "ok"


class PumpCommand(BaseModel):
    running: bool


class PumpCommandResponse(BaseModel):
    accepted: bool = True
    state: ProcessState


class ScenarioName(StrEnum):
    normal = "normal"
    high_tank = "high_tank"


class ScenarioCommand(BaseModel):
    scenario: ScenarioName
