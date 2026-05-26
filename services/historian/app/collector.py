"""Background poll loop: fetch state from plc-simulator and persist."""

from __future__ import annotations

import asyncio
import logging
import os

import httpx

from . import db
from .models import ProcessStatePayload

log = logging.getLogger(__name__)


PLC_URL = os.getenv("PLC_SIMULATOR_URL", "http://plc-simulator:8000")
POLL_INTERVAL = float(os.getenv("HISTORIAN_POLL_INTERVAL_SECONDS", "2.0"))


async def poll_loop(client: httpx.AsyncClient) -> None:
    state_url = f"{PLC_URL}/api/state"
    log.info("Historian poll loop starting: %s every %.2fs", state_url, POLL_INTERVAL)
    while True:
        try:
            await asyncio.sleep(POLL_INTERVAL)
            try:
                resp = await client.get(state_url, timeout=5.0)
                resp.raise_for_status()
                payload = ProcessStatePayload.model_validate(resp.json())
                db.insert_reading(payload)
            except httpx.HTTPError as err:
                log.warning("Poll failed (network): %s", err)
            except Exception as err:
                # Never crash the loop. DB issues are recoverable on the next tick.
                log.warning("Poll failed: %s", err)
        except asyncio.CancelledError:
            log.info("Historian poll loop cancelled")
            raise
