-- ADA v3: action_plans table (dedicated plans linked to opportunities)
CREATE TABLE IF NOT EXISTS ada_core.action_plans (
    id SERIAL PRIMARY KEY,
    opportunity_id INTEGER REFERENCES ada_core.opportunities(id) ON DELETE SET NULL,
    plan TEXT NOT NULL,
    status VARCHAR(64) NOT NULL DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_ada_core_action_plans_opportunity ON ada_core.action_plans (opportunity_id);
CREATE INDEX IF NOT EXISTS idx_ada_core_action_plans_status ON ada_core.action_plans (status);
CREATE INDEX IF NOT EXISTS idx_ada_core_action_plans_created ON ada_core.action_plans (created_at DESC);
