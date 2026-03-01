-- Schema para decisiones del decision-engine (y políticas si se desea)
CREATE SCHEMA IF NOT EXISTS ada_decisions;

CREATE TABLE IF NOT EXISTS ada_decisions.decisions (
    id SERIAL PRIMARY KEY,
    proposal_id VARCHAR(255),
    decision VARCHAR(50) NOT NULL,
    simulation_result JSONB,
    policy_approved BOOLEAN,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_ada_decisions_created_at ON ada_decisions.decisions (created_at);
CREATE INDEX IF NOT EXISTS idx_ada_decisions_proposal ON ada_decisions.decisions (proposal_id);
