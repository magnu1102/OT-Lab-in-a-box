"""FastAPI entrypoint for the PLC simulator.

This service simulates a water-tank process for the OT Lab-in-a-Box project.
It is a teaching simulation only — it does not implement any real industrial
control protocol and must not be connected to real equipment.
"""

from __future__ import annotations

import asyncio
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .models import (
    HealthResponse,
    ProcessState,
    PumpCommand,
    PumpCommandResponse,
)
from .process import WaterTankProcess

SIM_TICK_SECONDS = float(os.getenv("SIM_TICK_SECONDS", "0.5"))
HMI_PORT = os.getenv("HMI_PORT", "3000")

process = WaterTankProcess()


async def _simulation_loop() -> None:
    while True:
        await asyncio.sleep(SIM_TICK_SECONDS)
        process.step(SIM_TICK_SECONDS)


@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(_simulation_loop())
    try:
        yield
    finally:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass


app = FastAPI(
    title="OT Lab PLC Simulator",
    description="Simulated water-tank process device. Educational / defensive only.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[f"http://localhost:{HMI_PORT}"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


def _current_state() -> ProcessState:
    return ProcessState(
        tank_level=round(process.tank_level, 2),
        pump_running=process.pump_running,
        inflow_rate=process.inflow_rate,
        outflow_rate=process.outflow_rate,
        temperature=round(process.temperature, 2),
        alarm=process.alarm,
        last_updated=process.last_updated,
    )


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse()


@app.get("/api/state", response_model=ProcessState)
def get_state() -> ProcessState:
    return _current_state()


@app.post("/api/control/pump", response_model=PumpCommandResponse)
def control_pump(command: PumpCommand) -> PumpCommandResponse:
    """Toggle the simulated pump.

    Safety note: this affects the in-memory simulation only. It is not a
    write to any real PLC or control device.
    """
    process.set_pump(command.running)
    return PumpCommandResponse(accepted=True, state=_current_state())


@app.post("/api/sim/reset", response_model=ProcessState)
def reset_sim() -> ProcessState:
    process.reset()
    return _current_state()
