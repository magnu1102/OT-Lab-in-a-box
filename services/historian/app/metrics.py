"""Prometheus metrics for the historian."""

from prometheus_client import Counter, Gauge, Histogram

POLLS_TOTAL = Counter(
    "ot_lab_historian_polls_total",
    "Total polls of the plc-simulator state endpoint.",
    ["result"],
)
ROWS_INSERTED_TOTAL = Counter(
    "ot_lab_historian_rows_inserted_total",
    "Process readings inserted into Postgres.",
)
POLL_DURATION = Histogram(
    "ot_lab_historian_poll_duration_seconds",
    "Time spent fetching and persisting one reading.",
    buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0),
)
LAST_POLL_TIMESTAMP = Gauge(
    "ot_lab_historian_last_poll_timestamp_seconds",
    "Unix timestamp of the last successful poll.",
)
QUERIES_TOTAL = Counter(
    "ot_lab_historian_queries_total",
    "Read queries served by the historian.",
    ["endpoint"],
)
DB_UP = Gauge(
    "ot_lab_historian_db_up",
    "1 if the historian can reach Postgres, 0 otherwise.",
)
