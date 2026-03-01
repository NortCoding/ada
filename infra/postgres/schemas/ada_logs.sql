-- Schema para auditoría y trazabilidad (logging-system)
CREATE SCHEMA IF NOT EXISTS ada_logs;

CREATE TABLE IF NOT EXISTS ada_logs.events (
    id SERIAL PRIMARY KEY,
    service_name VARCHAR(50) NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    payload JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_ada_logs_events_created_at ON ada_logs.events (created_at);
CREATE INDEX IF NOT EXISTS idx_ada_logs_events_service_type ON ada_logs.events (service_name, event_type);
