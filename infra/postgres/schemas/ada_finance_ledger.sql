-- Tabla transactions para financial-ledger (schema ada_finance ya existe)
CREATE TABLE IF NOT EXISTS ada_finance.transactions (
    id SERIAL PRIMARY KEY,
    type VARCHAR(50) NOT NULL,
    amount DECIMAL(18, 4) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_ada_finance_transactions_created_at ON ada_finance.transactions (created_at);
CREATE INDEX IF NOT EXISTS idx_ada_finance_transactions_type ON ada_finance.transactions (type);
