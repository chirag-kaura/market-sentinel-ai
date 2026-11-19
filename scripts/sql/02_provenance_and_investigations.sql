-- ============================================================================
-- MARKET SENTINEL AI — MIGRATION 02: PROVENANCE COLUMNS & INVESTIGATIONS
-- Description: Adds immutable provenance metadata to daily market quotes and
-- creates tables for persistent investigation cases and analyst dispositions.
-- ============================================================================

-- 1. Add provenance audit columns to market_quotes_daily
ALTER TABLE market_quotes_daily
    ADD COLUMN IF NOT EXISTS retrieval_timestamp_utc TIMESTAMPTZ DEFAULT NOW(),
    ADD COLUMN IF NOT EXISTS original_source_url VARCHAR(1000),
    ADD COLUMN IF NOT EXISTS content_hash VARCHAR(64);

CREATE INDEX IF NOT EXISTS idx_mkt_quotes_content_hash ON market_quotes_daily(content_hash);

-- 2. Create investigation_cases table if not exists
CREATE TABLE IF NOT EXISTS investigation_cases (
    case_id VARCHAR(64) PRIMARY KEY,
    alert_id VARCHAR(64) NOT NULL,
    ticker VARCHAR(32) NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'OPEN',
    analyst_notes TEXT,
    assigned_analyst VARCHAR(64),
    dossier_text TEXT,
    evidence_count INT NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_investigation_cases_alert ON investigation_cases(alert_id);
CREATE INDEX IF NOT EXISTS idx_investigation_cases_ticker ON investigation_cases(ticker);
CREATE INDEX IF NOT EXISTS idx_investigation_cases_status ON investigation_cases(status);

-- 3. Create analyst_dispositions table if not exists
CREATE TABLE IF NOT EXISTS analyst_dispositions (
    id VARCHAR(36) PRIMARY KEY,
    case_id VARCHAR(64) NOT NULL REFERENCES investigation_cases(case_id) ON DELETE CASCADE,
    alert_id VARCHAR(64) NOT NULL,
    analyst_username VARCHAR(64) NOT NULL,
    action VARCHAR(50) NOT NULL,
    disposition_notes TEXT NOT NULL,
    reviewed_at_utc TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_dispositions_case ON analyst_dispositions(case_id);
CREATE INDEX IF NOT EXISTS idx_dispositions_analyst ON analyst_dispositions(analyst_username);
