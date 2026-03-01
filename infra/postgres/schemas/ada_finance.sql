-- Schema para registro económico interno (financial-ledger)
CREATE SCHEMA IF NOT EXISTS ada_finance;

CREATE TABLE IF NOT EXISTS ada_finance.entries (
    id SERIAL PRIMARY KEY,
    entry_type VARCHAR(50) NOT NULL,
    amount DECIMAL(18, 4) NOT NULL,
    currency VARCHAR(10) DEFAULT 'USD',
    reference_id VARCHAR(255),
    payload JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_ada_finance_entries_created_at ON ada_finance.entries (created_at);
CREATE INDEX IF NOT EXISTS idx_ada_finance_entries_reference ON ada_finance.entries (reference_id);
