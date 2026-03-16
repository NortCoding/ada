-- ADA v2 Minimal Core: goals, memories, ideas for strategic agent
CREATE SCHEMA IF NOT EXISTS ada_core;

CREATE TABLE IF NOT EXISTS ada_core.goals (
    id SERIAL PRIMARY KEY,
    goal TEXT NOT NULL,
    status VARCHAR(64) NOT NULL DEFAULT 'active',
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_ada_core_goals_status ON ada_core.goals (status);

CREATE TABLE IF NOT EXISTS ada_core.memories (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT NOW(),
    topic VARCHAR(255),
    content TEXT NOT NULL,
    importance INTEGER DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_ada_core_memories_topic ON ada_core.memories (topic);
CREATE INDEX IF NOT EXISTS idx_ada_core_memories_timestamp ON ada_core.memories (timestamp DESC);

CREATE TABLE IF NOT EXISTS ada_core.ideas (
    id SERIAL PRIMARY KEY,
    goal_id INTEGER REFERENCES ada_core.goals(id) ON DELETE SET NULL,
    idea TEXT NOT NULL,
    score NUMERIC(5,2) DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_ada_core_ideas_goal_id ON ada_core.ideas (goal_id);
CREATE INDEX IF NOT EXISTS idx_ada_core_ideas_created_at ON ada_core.ideas (created_at DESC);

-- ADA v2.5: experiencias (eventos + aprendizaje) y oportunidades (ideas evaluadas)
CREATE TABLE IF NOT EXISTS ada_core.experiences (
    id SERIAL PRIMARY KEY,
    event TEXT NOT NULL,
    result TEXT,
    learning TEXT,
    timestamp TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_ada_core_experiences_timestamp ON ada_core.experiences (timestamp DESC);

CREATE TABLE IF NOT EXISTS ada_core.opportunities (
    id SERIAL PRIMARY KEY,
    idea TEXT NOT NULL,
    score NUMERIC(5,2) DEFAULT 0,
    impact NUMERIC(4,2) DEFAULT 0,
    ease NUMERIC(4,2) DEFAULT 0,
    speed NUMERIC(4,2) DEFAULT 0,
    risk NUMERIC(4,2) DEFAULT 0,
    status VARCHAR(64) NOT NULL DEFAULT 'pending',
    goal_id INTEGER REFERENCES ada_core.goals(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_ada_core_opportunities_status ON ada_core.opportunities (status);
CREATE INDEX IF NOT EXISTS idx_ada_core_opportunities_score ON ada_core.opportunities (score DESC);
CREATE INDEX IF NOT EXISTS idx_ada_core_opportunities_goal_id ON ada_core.opportunities (goal_id);
