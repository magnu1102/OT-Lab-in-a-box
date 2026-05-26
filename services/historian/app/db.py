"""PostgreSQL access for the historian.

Owns a small psycopg connection pool. The pool is created and opened by
`main.lifespan` and closed on shutdown.
"""

from __future__ import annotations

import logging
import os
import time
from datetime import datetime

from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from .models import ProcessStatePayload, Reading

log = logging.getLogger(__name__)

_pool: ConnectionPool | None = None


def _dsn() -> str:
    host = os.getenv("POSTGRES_HOST", "postgres")
    port = os.getenv("POSTGRES_PORT", "5432")
    db = os.getenv("POSTGRES_DB", "ot_lab")
    user = os.getenv("POSTGRES_USER", "ot_lab")
    password = os.getenv("POSTGRES_PASSWORD", "change_me")
    return f"host={host} port={port} dbname={db} user={user} password={password}"


def open_pool(max_wait_seconds: float = 30.0) -> None:
    """Open the global pool, retrying briefly for Postgres to accept connections."""
    global _pool
    pool = ConnectionPool(_dsn(), min_size=1, max_size=4, open=False)
    deadline = time.monotonic() + max_wait_seconds
    last_err: Exception | None = None
    while time.monotonic() < deadline:
        try:
            pool.open(wait=True, timeout=5.0)
            _pool = pool
            log.info("Postgres pool opened")
            return
        except Exception as err:  # pragma: no cover - timing-dependent
            last_err = err
            log.warning("Postgres not ready yet: %s", err)
            time.sleep(1.0)
    raise RuntimeError(f"Could not connect to Postgres within {max_wait_seconds}s: {last_err}")


def close_pool() -> None:
    global _pool
    if _pool is not None:
        _pool.close()
        _pool = None


def _require_pool() -> ConnectionPool:
    if _pool is None:
        raise RuntimeError("Connection pool not initialized")
    return _pool


def insert_reading(payload: ProcessStatePayload) -> None:
    pool = _require_pool()
    with pool.connection() as conn, conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO process_readings
                (timestamp, tank_level, pump_running, temperature, alarm)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (
                payload.last_updated,
                payload.tank_level,
                payload.pump_running,
                payload.temperature,
                payload.alarm,
            ),
        )


def fetch_readings(limit: int, since: datetime | None = None) -> list[Reading]:
    pool = _require_pool()
    with pool.connection() as conn, conn.cursor(row_factory=dict_row) as cur:
        if since is None:
            cur.execute(
                """
                SELECT id, timestamp, tank_level, pump_running, temperature, alarm
                FROM process_readings
                ORDER BY timestamp DESC
                LIMIT %s
                """,
                (limit,),
            )
        else:
            cur.execute(
                """
                SELECT id, timestamp, tank_level, pump_running, temperature, alarm
                FROM process_readings
                WHERE timestamp >= %s
                ORDER BY timestamp DESC
                LIMIT %s
                """,
                (since, limit),
            )
        return [Reading(**row) for row in cur.fetchall()]


def ping() -> bool:
    try:
        pool = _require_pool()
        with pool.connection() as conn, conn.cursor() as cur:
            cur.execute("SELECT 1")
            cur.fetchone()
        return True
    except Exception as err:
        log.warning("Postgres ping failed: %s", err)
        return False
