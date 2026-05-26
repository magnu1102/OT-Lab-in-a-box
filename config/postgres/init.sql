CREATE TABLE IF NOT EXISTS process_readings (
    id           SERIAL PRIMARY KEY,
    timestamp    TIMESTAMPTZ NOT NULL,
    tank_level   DOUBLE PRECISION NOT NULL,
    pump_running BOOLEAN NOT NULL,
    temperature  DOUBLE PRECISION NOT NULL,
    alarm        BOOLEAN NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_process_readings_timestamp
    ON process_readings (timestamp DESC);
