"""FastAPI entrypoint for the historian.

Polls plc-simulator on an interval and persists readings to PostgreSQL.
Exposes a small read-back API for the HMI.
"""

from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Optional

import httpx
from fastapi import FastAPI, HTTPException, Query, Response
from prometheus_client import make_asgi_app

from . import collector, db, metrics
from .models import HealthResponse, Reading

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s - %(message)s",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    db.open_pool()
    async with httpx.AsyncClient() as client:
        task = asyncio.create_task(collector.poll_loop(client))
        try:
            yield
        finally:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
    db.close_pool()


app = FastAPI(
    title="OT Lab Historian",
    description="Stores process readings polled from plc-simulator. Educational / defensive only.",
    version="0.1.0",
    lifespan=lifespan,
)

app.mount("/metrics", make_asgi_app())


@app.get("/health", response_model=HealthResponse)
def health(response: Response) -> HealthResponse:
    db_ok = db.ping()
    metrics.DB_UP.set(1.0 if db_ok else 0.0)
    if not db_ok:
        response.status_code = 503
    return HealthResponse(status="ok" if db_ok else "degraded")


@app.get("/api/history/readings", response_model=list[Reading])
def get_readings(
    limit: int = Query(100, ge=1, le=1000),
    since: Optional[datetime] = Query(None, description="ISO-8601 timestamp; only newer rows returned."),
) -> list[Reading]:
    metrics.QUERIES_TOTAL.labels(endpoint="readings").inc()
    try:
        return db.fetch_readings(limit=limit, since=since)
    except Exception as err:
        raise HTTPException(status_code=503, detail=f"Database unavailable: {err}")
