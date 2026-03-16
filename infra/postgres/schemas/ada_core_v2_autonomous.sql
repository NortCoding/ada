-- ADA v2 Autonomous: derived_goals + experiences extended (success_score, evaluation)
-- Run after ada_core.sql. Safe to run multiple times (IF NOT EXISTS / DO blocks).

-- Derived goals (generated from parent goal + ideas)
CREATE TABLE IF NOT EXISTS ada_core.derived_goals (
    id SERIAL PRIMARY KEY,
    parent_goal_id INTEGER REFERENCES ada_core.goals(id) ON DELETE SET NULL,
    goal TEXT NOT NULL,
    status VARCHAR(64) NOT NULL DEFAULT 'active',
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_ada_core_derived_goals_parent ON ada_core.derived_goals (parent_goal_id);
CREATE INDEX IF NOT EXISTS idx_ada_core_derived_goals_status ON ada_core.derived_goals (status);

-- Extend experiences with success_score and evaluation (for learning from results)
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = 'ada_core' AND table_name = 'experiences' AND column_name = 'success_score') THEN
        ALTER TABLE ada_core.experiences ADD COLUMN success_score DOUBLE PRECISION;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = 'ada_core' AND table_name = 'experiences' AND column_name = 'evaluation') THEN
        ALTER TABLE ada_core.experiences ADD COLUMN evaluation TEXT;
    END IF;
END $$;
