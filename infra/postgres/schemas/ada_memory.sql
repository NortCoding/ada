-- Schema para estado y contexto del agente (memory-db)
CREATE SCHEMA IF NOT EXISTS ada_memory;

CREATE TABLE IF NOT EXISTS ada_memory.context (
    id SERIAL PRIMARY KEY,
    key VARCHAR(255) NOT NULL UNIQUE,
    value JSONB NOT NULL,
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_ada_memory_context_key ON ada_memory.context (key);
