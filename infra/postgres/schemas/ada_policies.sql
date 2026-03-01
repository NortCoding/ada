-- Schema para reglas de gobernanza (policy-engine)
CREATE SCHEMA IF NOT EXISTS ada_policies;

CREATE TABLE IF NOT EXISTS ada_policies.rules (
    id SERIAL PRIMARY KEY,
    action_type VARCHAR(100) NOT NULL,
    active BOOLEAN NOT NULL DEFAULT true,
    name VARCHAR(255),
    config JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_ada_policies_rules_action_active ON ada_policies.rules (action_type, active);

-- Regla de prueba: aprobar test_mvp (primer ciclo F2+F3)
INSERT INTO ada_policies.rules (action_type, active, name)
VALUES ('test_mvp', true, 'Prueba MVP');

-- Directrices: aprendizaje no requiere aprobación humana (solo se muestra)
INSERT INTO ada_policies.rules (action_type, active, name)
VALUES ('store_learning', true, 'Aprendizaje autónomo'),
       ('learning', true, 'Aprendizaje'),
       ('record_insight', true, 'Registro de insight'),
       ('update_score', true, 'Actualizar score');

-- Modo "feedback supervisado": auto-aprobación cuando métricas son seguras (ROI > 0.6, riesgo < 0.2).
-- La decisión se registra como "aprobación simulada" en logging y memory-db para aprendizaje.
-- config: roi_min, risk_max, simulated_approval (opcional: action_type '*' = cualquier acción).
INSERT INTO ada_policies.rules (action_type, active, name, config)
VALUES (
  '*',
  true,
  'test_auto_approve',
  '{"roi_min": 0.6, "risk_max": 0.2, "simulated_approval": true, "notes": "Modo de prueba supervisada para aprendizaje"}'::jsonb
);
