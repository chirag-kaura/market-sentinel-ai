-- ============================================================================
-- MARKET SENTINEL AI — INITIAL DATABASE DDL MIGRATION
-- Migration Version: 01_initial_schema.sql
-- Description: Core tables, constraints, indexes, and pgvector extension
-- Target Database: PostgreSQL 16+ with pgvector
-- ============================================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";

-- ----------------------------------------------------------------------------
-- 1. Table: symbol_master
-- Canonical company and symbol reference master
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS symbol_master (
    symbol VARCHAR(20) PRIMARY KEY,
    company_name VARCHAR(255) NOT NULL,
    isin VARCHAR(12) NOT NULL UNIQUE,
    sector VARCHAR(100) NOT NULL,
    industry VARCHAR(150) NOT NULL,
    exchange VARCHAR(10) NOT NULL DEFAULT 'NSE',
    series VARCHAR(5) NOT NULL DEFAULT 'EQ',
    listing_date DATE NOT NULL,
    market_cap_tier VARCHAR(20) NOT NULL CHECK (market_cap_tier IN ('LARGE_CAP', 'MID_CAP', 'SMALL_CAP')),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    aliases JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at_utc TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at_utc TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_symbol_master_isin ON symbol_master(isin);
CREATE INDEX IF NOT EXISTS idx_symbol_master_sector ON symbol_master(sector);

-- ----------------------------------------------------------------------------
-- 2. Table: market_quotes_daily
-- Authentic historical and daily end-of-day OHLCV + delivery data
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS market_quotes_daily (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    symbol VARCHAR(20) NOT NULL REFERENCES symbol_master(symbol) ON DELETE CASCADE,
    trade_date DATE NOT NULL,
    open_price NUMERIC(12, 2) NOT NULL CHECK (open_price > 0),
    high_price NUMERIC(12, 2) NOT NULL,
    low_price NUMERIC(12, 2) NOT NULL CHECK (low_price > 0),
    close_price NUMERIC(12, 2) NOT NULL CHECK (close_price > 0),
    volume BIGINT NOT NULL CHECK (volume >= 0),
    turnover NUMERIC(18, 2) NOT NULL CHECK (turnover >= 0),
    delivery_qty BIGINT CHECK (delivery_qty >= 0),
    delivery_pct NUMERIC(6, 2) CHECK (delivery_pct >= 0 AND delivery_pct <= 100),
    source_provider VARCHAR(50) NOT NULL,
    retrieval_timestamp_utc TIMESTAMPTZ DEFAULT NOW(),
    original_source_url VARCHAR(1000),
    content_hash VARCHAR(64),
    ingested_at_utc TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_high_low_valid CHECK (high_price >= low_price),
    CONSTRAINT chk_high_open_valid CHECK (high_price >= open_price),
    CONSTRAINT chk_high_close_valid CHECK (high_price >= close_price),
    CONSTRAINT uq_market_quotes_symbol_date UNIQUE (symbol, trade_date)
);

CREATE INDEX IF NOT EXISTS idx_mkt_quotes_symbol_date ON market_quotes_daily(symbol, trade_date DESC);
CREATE INDEX IF NOT EXISTS idx_mkt_quotes_date ON market_quotes_daily(trade_date DESC);

-- ----------------------------------------------------------------------------
-- 3. Table: corporate_announcements
-- Official regulatory filings and company announcements
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS corporate_announcements (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    symbol VARCHAR(20) NOT NULL REFERENCES symbol_master(symbol) ON DELETE CASCADE,
    category VARCHAR(100) NOT NULL,
    subject VARCHAR(500) NOT NULL,
    body_text TEXT,
    attachment_url VARCHAR(1000),
    published_at_utc TIMESTAMPTZ NOT NULL,
    ingested_at_utc TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    source_provider VARCHAR(50) NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_corp_announcements_symbol_time ON corporate_announcements(symbol, published_at_utc DESC);
CREATE INDEX IF NOT EXISTS idx_corp_announcements_category ON corporate_announcements(category);

-- ----------------------------------------------------------------------------
-- 4. Table: news_articles
-- Public financial media articles and RSS feed items
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS news_articles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    canonical_url VARCHAR(1000) NOT NULL UNIQUE,
    title VARCHAR(500) NOT NULL,
    summary TEXT,
    body_text TEXT,
    source_outlet VARCHAR(100) NOT NULL,
    published_at_utc TIMESTAMPTZ NOT NULL,
    ingested_at_utc TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    sentiment_score NUMERIC(4, 3) CHECK (sentiment_score >= -1.0 AND sentiment_score <= 1.0)
);

CREATE INDEX IF NOT EXISTS idx_news_articles_pub_time ON news_articles(published_at_utc DESC);
CREATE INDEX IF NOT EXISTS idx_news_articles_source ON news_articles(source_outlet);

-- ----------------------------------------------------------------------------
-- 5. Table: document_chunks
-- Chunked documents with vector embeddings for semantic retrieval via pgvector
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS document_chunks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    parent_type VARCHAR(30) NOT NULL CHECK (parent_type IN ('CORPORATE_ANNOUNCEMENT', 'NEWS_ARTICLE')),
    parent_id UUID NOT NULL,
    symbol VARCHAR(20) REFERENCES symbol_master(symbol) ON DELETE CASCADE,
    chunk_index INT NOT NULL,
    chunk_text TEXT NOT NULL,
    embedding vector(384), -- Standard 384-dim CPU-optimized SentenceTransformer (all-MiniLM-L6-v2)
    created_at_utc TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_doc_chunks_symbol ON document_chunks(symbol);
CREATE INDEX IF NOT EXISTS idx_doc_chunks_parent ON document_chunks(parent_type, parent_id);
-- HNSW index for high-speed cosine vector similarity search
CREATE INDEX IF NOT EXISTS idx_doc_chunks_embedding ON document_chunks USING hnsw (embedding vector_cosine_ops);

-- ----------------------------------------------------------------------------
-- 6. Table: market_features_daily
-- Chronological financial features computed strictly on prior historical data
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS market_features_daily (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    symbol VARCHAR(20) NOT NULL REFERENCES symbol_master(symbol) ON DELETE CASCADE,
    feature_date DATE NOT NULL,
    return_daily NUMERIC(10, 6) NOT NULL,
    return_log NUMERIC(10, 6) NOT NULL,
    return_roll_20d NUMERIC(10, 6) NOT NULL,
    volatility_roll_20d NUMERIC(10, 6) NOT NULL CHECK (volatility_roll_20d >= 0),
    volume_ratio_20d NUMERIC(10, 4) NOT NULL CHECK (volume_ratio_20d >= 0),
    volume_zscore_20d NUMERIC(8, 4) NOT NULL,
    price_gap NUMERIC(10, 6) NOT NULL,
    delivery_zscore_20d NUMERIC(8, 4),
    created_at_utc TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_mkt_features_symbol_date UNIQUE (symbol, feature_date)
);

CREATE INDEX IF NOT EXISTS idx_mkt_features_symbol_date ON market_features_daily(symbol, feature_date DESC);

-- ----------------------------------------------------------------------------
-- 7. Table: anomaly_scores
-- Statistical and machine learning anomaly detection scores
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS anomaly_scores (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    symbol VARCHAR(20) NOT NULL REFERENCES symbol_master(symbol) ON DELETE CASCADE,
    score_date DATE NOT NULL,
    baseline_zscore NUMERIC(8, 4) NOT NULL,
    isoforest_score NUMERIC(8, 6) NOT NULL CHECK (isoforest_score >= 0.0 AND isoforest_score <= 1.0),
    is_anomaly BOOLEAN NOT NULL DEFAULT FALSE,
    feature_snapshot JSONB NOT NULL,
    model_version VARCHAR(50) NOT NULL,
    created_at_utc TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_anomaly_scores_symbol_date UNIQUE (symbol, score_date)
);

CREATE INDEX IF NOT EXISTS idx_anomaly_scores_symbol_date ON anomaly_scores(symbol, score_date DESC);
CREATE INDEX IF NOT EXISTS idx_anomaly_scores_is_anomaly ON anomaly_scores(is_anomaly);

-- ----------------------------------------------------------------------------
-- 8. Table: volatility_forecasts
-- Econometric volatility estimates and conditional clustering forecasts
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS volatility_forecasts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    symbol VARCHAR(20) NOT NULL REFERENCES symbol_master(symbol) ON DELETE CASCADE,
    forecast_date DATE NOT NULL,
    model_type VARCHAR(50) NOT NULL CHECK (model_type IN ('EWMA', 'GARCH_1_1', 'HISTORICAL_ROLLING')),
    horizon_days INT NOT NULL DEFAULT 5,
    forecast_volatility NUMERIC(10, 6) NOT NULL CHECK (forecast_volatility > 0),
    ci_lower_95 NUMERIC(10, 6) CHECK (ci_lower_95 >= 0),
    ci_upper_95 NUMERIC(10, 6),
    model_version VARCHAR(50) NOT NULL,
    created_at_utc TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_ci_bounds CHECK (ci_upper_95 IS NULL OR ci_upper_95 >= ci_lower_95)
);

CREATE INDEX IF NOT EXISTS idx_vol_forecasts_symbol_date ON volatility_forecasts(symbol, forecast_date DESC);

-- ----------------------------------------------------------------------------
-- 9. Table: risk_alerts
-- Prioritized risk alerts synthesizing anomalies, volatility, and news context
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS risk_alerts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    symbol VARCHAR(20) NOT NULL REFERENCES symbol_master(symbol) ON DELETE CASCADE,
    alert_date DATE NOT NULL,
    risk_score NUMERIC(5, 2) NOT NULL CHECK (risk_score >= 0.0 AND risk_score <= 100.0),
    priority_tier VARCHAR(20) NOT NULL CHECK (priority_tier IN ('CRITICAL', 'HIGH', 'MEDIUM', 'LOW')),
    alert_category VARCHAR(50) NOT NULL,
    anomaly_score_id UUID REFERENCES anomaly_scores(id) ON DELETE SET NULL,
    has_matching_news BOOLEAN NOT NULL DEFAULT FALSE,
    dossier_status VARCHAR(30) NOT NULL DEFAULT 'PENDING' CHECK (dossier_status IN ('PENDING', 'GENERATED', 'FAILED')),
    review_status VARCHAR(30) NOT NULL DEFAULT 'UNREVIEWED' CHECK (review_status IN ('UNREVIEWED', 'ESCALATED', 'DISMISSED')),
    created_at_utc TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_risk_alerts_symbol_date ON risk_alerts(symbol, alert_date DESC);
CREATE INDEX IF NOT EXISTS idx_risk_alerts_priority ON risk_alerts(priority_tier);
CREATE INDEX IF NOT EXISTS idx_risk_alerts_review ON risk_alerts(review_status);

-- ----------------------------------------------------------------------------
-- 10. Table: analyst_dispositions
-- Regulatory audit log of human compliance reviews, escalations, and notes
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS analyst_dispositions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    alert_id UUID NOT NULL REFERENCES risk_alerts(id) ON DELETE CASCADE,
    user_id UUID NOT NULL,
    action VARCHAR(50) NOT NULL CHECK (action IN ('ESCALATE_TO_SAR', 'DISMISS_LEGITIMATE', 'REQUEST_INFO')),
    disposition_notes TEXT NOT NULL CHECK (length(disposition_notes) >= 10),
    reviewed_at_utc TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_dispositions_alert ON analyst_dispositions(alert_id);
CREATE INDEX IF NOT EXISTS idx_dispositions_user ON analyst_dispositions(user_id);
