-- Schema para tareas ejecutadas por task-runner
CREATE SCHEMA IF NOT EXISTS ada_tasks;

CREATE TABLE IF NOT EXISTS ada_tasks.runs (
    id SERIAL PRIMARY KEY,
    task_type VARCHAR(100) NOT NULL,
    status VARCHAR(50) NOT NULL,
    input_payload JSONB,
    output_payload JSONB,
    started_at TIMESTAMP DEFAULT NOW(),
    finished_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_ada_tasks_runs_status ON ada_tasks.runs (status);
CREATE INDEX IF NOT EXISTS idx_ada_tasks_runs_started_at ON ada_tasks.runs (started_at);
