-- NoRugs PostgreSQL Database
-- Designed for web-scraper ingestion, historical analysis, risk scoring,
-- watchlists, alerts, and front-end API queries.

BEGIN;

CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- =========================================================
-- 1. ENUM TYPES
-- =========================================================

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'risk_level') THEN
        CREATE TYPE risk_level AS ENUM ('LOW', 'MODERATE', 'HIGH', 'CRITICAL', 'UNKNOWN');
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'scrape_status') THEN
        CREATE TYPE scrape_status AS ENUM ('RUNNING', 'SUCCESS', 'PARTIAL', 'FAILED');
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'alert_type') THEN
        CREATE TYPE alert_type AS ENUM (
            'RISK_SCORE_CHANGE',
            'PRICE_CHANGE',
            'LIQUIDITY_CHANGE',
            'HOLDER_CONCENTRATION',
            'SUSPICIOUS_TRANSACTION',
            'CONTRACT_WARNING'
        );
    END IF;
END
$$;

-- =========================================================
-- 2. DATA SOURCES AND SCRAPER RUNS
-- =========================================================

CREATE TABLE IF NOT EXISTS data_sources (
    source_id       BIGSERIAL PRIMARY KEY,
    source_name     VARCHAR(100) NOT NULL UNIQUE,
    base_url        TEXT,
    source_type     VARCHAR(50) NOT NULL,
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    rate_limit_per_minute INTEGER,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS scraper_runs (
    scraper_run_id  BIGSERIAL PRIMARY KEY,
    source_id       BIGINT NOT NULL REFERENCES data_sources(source_id),
    status          scrape_status NOT NULL DEFAULT 'RUNNING',
    started_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at    TIMESTAMPTZ,
    records_found   INTEGER NOT NULL DEFAULT 0,
    records_inserted INTEGER NOT NULL DEFAULT 0,
    records_updated INTEGER NOT NULL DEFAULT 0,
    error_message   TEXT,
    metadata        JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_scraper_runs_source_started
    ON scraper_runs(source_id, started_at DESC);

-- Stores the original response for audit/debugging.
CREATE TABLE IF NOT EXISTS raw_scraped_data (
    raw_data_id     BIGSERIAL PRIMARY KEY,
    scraper_run_id  BIGINT REFERENCES scraper_runs(scraper_run_id) ON DELETE SET NULL,
    source_id       BIGINT NOT NULL REFERENCES data_sources(source_id),
    external_id     TEXT,
    request_url     TEXT,
    payload         JSONB NOT NULL,
    payload_hash    TEXT,
    scraped_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    processed       BOOLEAN NOT NULL DEFAULT FALSE,
    processing_error TEXT
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_raw_scraped_payload
    ON raw_scraped_data(source_id, payload_hash)
    WHERE payload_hash IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_raw_scraped_unprocessed
    ON raw_scraped_data(processed, scraped_at)
    WHERE processed = FALSE;

CREATE INDEX IF NOT EXISTS idx_raw_scraped_payload_gin
    ON raw_scraped_data USING GIN(payload);

-- =========================================================
-- 3. BLOCKCHAINS, EXCHANGES, AND CRYPTOCURRENCIES
-- =========================================================

CREATE TABLE IF NOT EXISTS blockchains (
    blockchain_id   BIGSERIAL PRIMARY KEY,
    name            VARCHAR(100) NOT NULL UNIQUE,
    symbol          VARCHAR(20),
    chain_identifier VARCHAR(100) UNIQUE,
    explorer_url    TEXT,
    native_currency VARCHAR(30),
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS exchanges (
    exchange_id     BIGSERIAL PRIMARY KEY,
    name            VARCHAR(150) NOT NULL UNIQUE,
    exchange_type   VARCHAR(30),
    website_url     TEXT,
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS cryptocurrencies (
    cryptocurrency_id BIGSERIAL PRIMARY KEY,
    external_market_id VARCHAR(150),
    blockchain_id   BIGINT REFERENCES blockchains(blockchain_id),
    name            VARCHAR(150) NOT NULL,
    symbol          VARCHAR(30) NOT NULL,
    contract_address VARCHAR(255),
    description     TEXT,
    website_url     TEXT,
    logo_url        TEXT,
    launch_date     DATE,
    decimals        INTEGER,
    total_supply    NUMERIC(38, 10),
    max_supply      NUMERIC(38, 10),
    circulating_supply NUMERIC(38, 10),
    is_verified     BOOLEAN NOT NULL DEFAULT FALSE,
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    metadata        JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT ck_crypto_decimals
        CHECK (decimals IS NULL OR decimals BETWEEN 0 AND 30),
    CONSTRAINT ck_crypto_supply
        CHECK (
            (total_supply IS NULL OR total_supply >= 0)
            AND (max_supply IS NULL OR max_supply >= 0)
            AND (circulating_supply IS NULL OR circulating_supply >= 0)
        )
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_crypto_market_id
    ON cryptocurrencies(external_market_id);

CREATE UNIQUE INDEX IF NOT EXISTS uq_crypto_contract
    ON cryptocurrencies(blockchain_id, LOWER(contract_address))
    WHERE contract_address IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_crypto_symbol
    ON cryptocurrencies(UPPER(symbol));

CREATE INDEX IF NOT EXISTS idx_crypto_name
    ON cryptocurrencies(LOWER(name));

-- Maps the same cryptocurrency across multiple data providers.
CREATE TABLE IF NOT EXISTS cryptocurrency_source_ids (
    cryptocurrency_id BIGINT NOT NULL
        REFERENCES cryptocurrencies(cryptocurrency_id) ON DELETE CASCADE,
    source_id       BIGINT NOT NULL
        REFERENCES data_sources(source_id) ON DELETE CASCADE,
    source_external_id TEXT NOT NULL,
    source_symbol   VARCHAR(50),
    source_slug     VARCHAR(150),
    last_seen_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (source_id, source_external_id),
    UNIQUE (cryptocurrency_id, source_id)
);

-- =========================================================
-- 4. MARKET AND LIQUIDITY HISTORY
-- =========================================================

CREATE TABLE IF NOT EXISTS market_snapshots (
    market_snapshot_id BIGSERIAL PRIMARY KEY,
    cryptocurrency_id BIGINT NOT NULL
        REFERENCES cryptocurrencies(cryptocurrency_id) ON DELETE CASCADE,
    source_id       BIGINT REFERENCES data_sources(source_id),
    price_usd       NUMERIC(38, 18),
    market_cap_usd  NUMERIC(38, 2),
    fully_diluted_valuation_usd NUMERIC(38, 2),
    volume_24h_usd  NUMERIC(38, 2),
    price_change_1h_pct NUMERIC(12, 6),
    price_change_24h_pct NUMERIC(12, 6),
    price_change_7d_pct NUMERIC(12, 6),
    circulating_supply NUMERIC(38, 10),
    total_supply    NUMERIC(38, 10),
    market_rank     INTEGER,
    observed_at     TIMESTAMPTZ NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT ck_market_nonnegative CHECK (
        (price_usd IS NULL OR price_usd >= 0)
        AND (market_cap_usd IS NULL OR market_cap_usd >= 0)
        AND (volume_24h_usd IS NULL OR volume_24h_usd >= 0)
    )
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_market_snapshot
    ON market_snapshots(cryptocurrency_id, source_id, observed_at);

CREATE INDEX IF NOT EXISTS idx_market_crypto_time
    ON market_snapshots(cryptocurrency_id, observed_at DESC);

CREATE INDEX IF NOT EXISTS idx_market_time
    ON market_snapshots(observed_at DESC);

CREATE TABLE IF NOT EXISTS liquidity_pools (
    liquidity_pool_id BIGSERIAL PRIMARY KEY,
    cryptocurrency_id BIGINT NOT NULL
        REFERENCES cryptocurrencies(cryptocurrency_id) ON DELETE CASCADE,
    blockchain_id   BIGINT REFERENCES blockchains(blockchain_id),
    exchange_id     BIGINT REFERENCES exchanges(exchange_id),
    pool_address    VARCHAR(255) NOT NULL,
    pair_symbol     VARCHAR(100),
    paired_token_address VARCHAR(255),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_liquidity_pool_address
    ON liquidity_pools(blockchain_id, LOWER(pool_address));

CREATE TABLE IF NOT EXISTS liquidity_snapshots (
    liquidity_snapshot_id BIGSERIAL PRIMARY KEY,
    liquidity_pool_id BIGINT NOT NULL
        REFERENCES liquidity_pools(liquidity_pool_id) ON DELETE CASCADE,
    source_id       BIGINT REFERENCES data_sources(source_id),
    liquidity_usd   NUMERIC(38, 2),
    token_reserve   NUMERIC(38, 10),
    paired_token_reserve NUMERIC(38, 10),
    volume_24h_usd  NUMERIC(38, 2),
    transactions_24h INTEGER,
    liquidity_locked BOOLEAN,
    lock_expiration TIMESTAMPTZ,
    observed_at     TIMESTAMPTZ NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT ck_liquidity_nonnegative CHECK (
        (liquidity_usd IS NULL OR liquidity_usd >= 0)
        AND (volume_24h_usd IS NULL OR volume_24h_usd >= 0)
        AND (transactions_24h IS NULL OR transactions_24h >= 0)
    )
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_liquidity_snapshot
    ON liquidity_snapshots(liquidity_pool_id, source_id, observed_at);

CREATE INDEX IF NOT EXISTS idx_liquidity_pool_time
    ON liquidity_snapshots(liquidity_pool_id, observed_at DESC);

-- =========================================================
-- 5. HOLDERS AND WALLET CONCENTRATION
-- =========================================================

CREATE TABLE IF NOT EXISTS wallets (
    wallet_id       BIGSERIAL PRIMARY KEY,
    blockchain_id   BIGINT NOT NULL REFERENCES blockchains(blockchain_id),
    wallet_address  VARCHAR(255) NOT NULL,
    label           VARCHAR(150),
    wallet_type     VARCHAR(50),
    is_contract     BOOLEAN NOT NULL DEFAULT FALSE,
    is_exchange     BOOLEAN NOT NULL DEFAULT FALSE,
    is_burn_address BOOLEAN NOT NULL DEFAULT FALSE,
    metadata        JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_wallet_address
    ON wallets(blockchain_id, LOWER(wallet_address));

CREATE TABLE IF NOT EXISTS holder_snapshots (
    holder_snapshot_id BIGSERIAL PRIMARY KEY,
    cryptocurrency_id BIGINT NOT NULL
        REFERENCES cryptocurrencies(cryptocurrency_id) ON DELETE CASCADE,
    wallet_id       BIGINT NOT NULL
        REFERENCES wallets(wallet_id) ON DELETE CASCADE,
    source_id       BIGINT REFERENCES data_sources(source_id),
    token_balance   NUMERIC(38, 10) NOT NULL DEFAULT 0,
    ownership_pct   NUMERIC(12, 8),
    holder_rank     INTEGER,
    observed_at     TIMESTAMPTZ NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT ck_ownership_pct
        CHECK (ownership_pct IS NULL OR ownership_pct BETWEEN 0 AND 100),
    CONSTRAINT ck_token_balance
        CHECK (token_balance >= 0)
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_holder_snapshot
    ON holder_snapshots(cryptocurrency_id, wallet_id, source_id, observed_at);

CREATE INDEX IF NOT EXISTS idx_holder_crypto_time_rank
    ON holder_snapshots(cryptocurrency_id, observed_at DESC, holder_rank);

CREATE TABLE IF NOT EXISTS concentration_snapshots (
    concentration_snapshot_id BIGSERIAL PRIMARY KEY,
    cryptocurrency_id BIGINT NOT NULL
        REFERENCES cryptocurrencies(cryptocurrency_id) ON DELETE CASCADE,
    source_id       BIGINT REFERENCES data_sources(source_id),
    holder_count    BIGINT,
    top_1_pct       NUMERIC(12, 8),
    top_5_pct       NUMERIC(12, 8),
    top_10_pct      NUMERIC(12, 8),
    top_20_pct      NUMERIC(12, 8),
    developer_wallet_pct NUMERIC(12, 8),
    exchange_wallet_pct NUMERIC(12, 8),
    burn_wallet_pct NUMERIC(12, 8),
    observed_at     TIMESTAMPTZ NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT ck_concentration_percentages CHECK (
        (top_1_pct IS NULL OR top_1_pct BETWEEN 0 AND 100)
        AND (top_5_pct IS NULL OR top_5_pct BETWEEN 0 AND 100)
        AND (top_10_pct IS NULL OR top_10_pct BETWEEN 0 AND 100)
        AND (top_20_pct IS NULL OR top_20_pct BETWEEN 0 AND 100)
        AND (developer_wallet_pct IS NULL OR developer_wallet_pct BETWEEN 0 AND 100)
        AND (exchange_wallet_pct IS NULL OR exchange_wallet_pct BETWEEN 0 AND 100)
        AND (burn_wallet_pct IS NULL OR burn_wallet_pct BETWEEN 0 AND 100)
    )
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_concentration_snapshot
    ON concentration_snapshots(cryptocurrency_id, source_id, observed_at);

CREATE INDEX IF NOT EXISTS idx_concentration_crypto_time
    ON concentration_snapshots(cryptocurrency_id, observed_at DESC);

-- =========================================================
-- 6. SMART CONTRACT AND SECURITY ANALYSIS
-- =========================================================

CREATE TABLE IF NOT EXISTS contract_assessments (
    contract_assessment_id BIGSERIAL PRIMARY KEY,
    cryptocurrency_id BIGINT NOT NULL
        REFERENCES cryptocurrencies(cryptocurrency_id) ON DELETE CASCADE,
    source_id       BIGINT REFERENCES data_sources(source_id),
    is_source_verified BOOLEAN,
    is_proxy_contract BOOLEAN,
    is_mintable     BOOLEAN,
    is_honeypot     BOOLEAN,
    buy_tax_pct     NUMERIC(10, 4),
    sell_tax_pct    NUMERIC(10, 4),
    ownership_renounced BOOLEAN,
    has_blacklist_function BOOLEAN,
    has_pause_function BOOLEAN,
    has_hidden_owner BOOLEAN,
    audit_status    VARCHAR(50),
    auditor_name    VARCHAR(150),
    vulnerability_count INTEGER NOT NULL DEFAULT 0,
    critical_vulnerability_count INTEGER NOT NULL DEFAULT 0,
    findings        JSONB NOT NULL DEFAULT '{}'::jsonb,
    observed_at     TIMESTAMPTZ NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT ck_contract_tax CHECK (
        (buy_tax_pct IS NULL OR buy_tax_pct BETWEEN 0 AND 100)
        AND (sell_tax_pct IS NULL OR sell_tax_pct BETWEEN 0 AND 100)
    ),
    CONSTRAINT ck_vulnerability_counts CHECK (
        vulnerability_count >= 0
        AND critical_vulnerability_count >= 0
    )
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_contract_assessment
    ON contract_assessments(cryptocurrency_id, source_id, observed_at);

CREATE INDEX IF NOT EXISTS idx_contract_crypto_time
    ON contract_assessments(cryptocurrency_id, observed_at DESC);

-- =========================================================
-- 7. TRANSACTION ACTIVITY
-- =========================================================

CREATE TABLE IF NOT EXISTS transaction_metrics (
    transaction_metric_id BIGSERIAL PRIMARY KEY,
    cryptocurrency_id BIGINT NOT NULL
        REFERENCES cryptocurrencies(cryptocurrency_id) ON DELETE CASCADE,
    source_id       BIGINT REFERENCES data_sources(source_id),
    transaction_count_1h BIGINT,
    transaction_count_24h BIGINT,
    unique_buyers_24h BIGINT,
    unique_sellers_24h BIGINT,
    buy_count_24h   BIGINT,
    sell_count_24h  BIGINT,
    buy_volume_24h_usd NUMERIC(38, 2),
    sell_volume_24h_usd NUMERIC(38, 2),
    large_transfer_count_24h BIGINT,
    suspicious_transaction_count BIGINT,
    average_transaction_usd NUMERIC(38, 2),
    observed_at     TIMESTAMPTZ NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT ck_transaction_counts CHECK (
        COALESCE(transaction_count_1h, 0) >= 0
        AND COALESCE(transaction_count_24h, 0) >= 0
        AND COALESCE(unique_buyers_24h, 0) >= 0
        AND COALESCE(unique_sellers_24h, 0) >= 0
        AND COALESCE(buy_count_24h, 0) >= 0
        AND COALESCE(sell_count_24h, 0) >= 0
        AND COALESCE(large_transfer_count_24h, 0) >= 0
        AND COALESCE(suspicious_transaction_count, 0) >= 0
    )
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_transaction_metric
    ON transaction_metrics(cryptocurrency_id, source_id, observed_at);

CREATE INDEX IF NOT EXISTS idx_transaction_crypto_time
    ON transaction_metrics(cryptocurrency_id, observed_at DESC);

CREATE TABLE IF NOT EXISTS suspicious_events (
    suspicious_event_id BIGSERIAL PRIMARY KEY,
    cryptocurrency_id BIGINT NOT NULL
        REFERENCES cryptocurrencies(cryptocurrency_id) ON DELETE CASCADE,
    wallet_id       BIGINT REFERENCES wallets(wallet_id),
    source_id       BIGINT REFERENCES data_sources(source_id),
    event_type      VARCHAR(100) NOT NULL,
    severity        SMALLINT NOT NULL,
    title           VARCHAR(255) NOT NULL,
    description     TEXT,
    transaction_hash VARCHAR(255),
    event_data      JSONB NOT NULL DEFAULT '{}'::jsonb,
    occurred_at     TIMESTAMPTZ NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT ck_suspicious_severity CHECK (severity BETWEEN 1 AND 10)
);

CREATE INDEX IF NOT EXISTS idx_suspicious_crypto_time
    ON suspicious_events(cryptocurrency_id, occurred_at DESC);

-- =========================================================
-- 8. DEVELOPER AND SOCIAL ACTIVITY
-- =========================================================

CREATE TABLE IF NOT EXISTS project_links (
    project_link_id BIGSERIAL PRIMARY KEY,
    cryptocurrency_id BIGINT NOT NULL
        REFERENCES cryptocurrencies(cryptocurrency_id) ON DELETE CASCADE,
    link_type       VARCHAR(50) NOT NULL,
    url             TEXT NOT NULL,
    username        VARCHAR(150),
    is_verified     BOOLEAN NOT NULL DEFAULT FALSE,
    UNIQUE (cryptocurrency_id, link_type, url)
);

CREATE TABLE IF NOT EXISTS developer_activity_snapshots (
    developer_activity_id BIGSERIAL PRIMARY KEY,
    cryptocurrency_id BIGINT NOT NULL
        REFERENCES cryptocurrencies(cryptocurrency_id) ON DELETE CASCADE,
    source_id       BIGINT REFERENCES data_sources(source_id),
    repository_count INTEGER,
    stars_count     INTEGER,
    forks_count     INTEGER,
    contributors_count INTEGER,
    commits_30d     INTEGER,
    issues_open     INTEGER,
    issues_closed_30d INTEGER,
    last_commit_at  TIMESTAMPTZ,
    observed_at     TIMESTAMPTZ NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_developer_activity
    ON developer_activity_snapshots(cryptocurrency_id, source_id, observed_at);

CREATE INDEX IF NOT EXISTS idx_developer_crypto_time
    ON developer_activity_snapshots(cryptocurrency_id, observed_at DESC);

CREATE TABLE IF NOT EXISTS social_activity_snapshots (
    social_activity_id BIGSERIAL PRIMARY KEY,
    cryptocurrency_id BIGINT NOT NULL
        REFERENCES cryptocurrencies(cryptocurrency_id) ON DELETE CASCADE,
    source_id       BIGINT REFERENCES data_sources(source_id),
    platform        VARCHAR(50) NOT NULL,
    follower_count  BIGINT,
    post_count_24h  INTEGER,
    mention_count_24h INTEGER,
    sentiment_score NUMERIC(8, 5),
    engagement_rate NUMERIC(10, 6),
    observed_at     TIMESTAMPTZ NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_social_crypto_time
    ON social_activity_snapshots(cryptocurrency_id, observed_at DESC);

-- =========================================================
-- 9. RISK-SCORING ENGINE
-- =========================================================

CREATE TABLE IF NOT EXISTS risk_models (
    risk_model_id   BIGSERIAL PRIMARY KEY,
    model_name      VARCHAR(150) NOT NULL,
    version         VARCHAR(50) NOT NULL,
    description     TEXT,
    configuration   JSONB NOT NULL DEFAULT '{}'::jsonb,
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (model_name, version)
);

CREATE TABLE IF NOT EXISTS risk_assessments (
    risk_assessment_id BIGSERIAL PRIMARY KEY,
    cryptocurrency_id BIGINT NOT NULL
        REFERENCES cryptocurrencies(cryptocurrency_id) ON DELETE CASCADE,
    risk_model_id   BIGINT REFERENCES risk_models(risk_model_id),
    overall_risk_score NUMERIC(5, 2) NOT NULL,
    risk_level      risk_level NOT NULL,
    confidence_score NUMERIC(5, 2),
    summary         TEXT,
    assessed_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT ck_risk_score CHECK (overall_risk_score BETWEEN 0 AND 100),
    CONSTRAINT ck_confidence_score CHECK (
        confidence_score IS NULL OR confidence_score BETWEEN 0 AND 100
    )
);

CREATE INDEX IF NOT EXISTS idx_risk_crypto_time
    ON risk_assessments(cryptocurrency_id, assessed_at DESC);

CREATE INDEX IF NOT EXISTS idx_risk_level_score
    ON risk_assessments(risk_level, overall_risk_score DESC);

CREATE TABLE IF NOT EXISTS risk_factor_scores (
    risk_factor_score_id BIGSERIAL PRIMARY KEY,
    risk_assessment_id BIGINT NOT NULL
        REFERENCES risk_assessments(risk_assessment_id) ON DELETE CASCADE,
    factor_name     VARCHAR(100) NOT NULL,
    factor_score    NUMERIC(5, 2) NOT NULL,
    weight          NUMERIC(6, 5) NOT NULL,
    weighted_score  NUMERIC(8, 4),
    explanation     TEXT,
    evidence        JSONB NOT NULL DEFAULT '{}'::jsonb,

    CONSTRAINT ck_factor_score CHECK (factor_score BETWEEN 0 AND 100),
    CONSTRAINT ck_factor_weight CHECK (weight BETWEEN 0 AND 1),
    UNIQUE (risk_assessment_id, factor_name)
);

-- =========================================================
-- 10. USERS, WATCHLISTS, AND ALERTS
-- =========================================================

CREATE TABLE IF NOT EXISTS app_users (
    user_id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email           VARCHAR(255) NOT NULL UNIQUE,
    password_hash   TEXT NOT NULL,
    display_name    VARCHAR(150),
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_login_at   TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS watchlists (
    watchlist_id    BIGSERIAL PRIMARY KEY,
    user_id         UUID NOT NULL REFERENCES app_users(user_id) ON DELETE CASCADE,
    name            VARCHAR(150) NOT NULL DEFAULT 'My Watchlist',
    description     TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (user_id, name)
);

CREATE TABLE IF NOT EXISTS watchlist_items (
    watchlist_id    BIGINT NOT NULL REFERENCES watchlists(watchlist_id) ON DELETE CASCADE,
    cryptocurrency_id BIGINT NOT NULL
        REFERENCES cryptocurrencies(cryptocurrency_id) ON DELETE CASCADE,
    added_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    notes           TEXT,
    PRIMARY KEY (watchlist_id, cryptocurrency_id)
);

CREATE TABLE IF NOT EXISTS alert_rules (
    alert_rule_id   BIGSERIAL PRIMARY KEY,
    user_id         UUID NOT NULL REFERENCES app_users(user_id) ON DELETE CASCADE,
    cryptocurrency_id BIGINT
        REFERENCES cryptocurrencies(cryptocurrency_id) ON DELETE CASCADE,
    alert_type      alert_type NOT NULL,
    threshold_value NUMERIC(38, 10),
    comparison_operator VARCHAR(10),
    is_enabled      BOOLEAN NOT NULL DEFAULT TRUE,
    configuration   JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT ck_alert_operator CHECK (
        comparison_operator IS NULL
        OR comparison_operator IN ('>', '>=', '<', '<=', '=', '!=')
    )
);

CREATE TABLE IF NOT EXISTS alert_events (
    alert_event_id  BIGSERIAL PRIMARY KEY,
    alert_rule_id   BIGINT REFERENCES alert_rules(alert_rule_id) ON DELETE SET NULL,
    user_id         UUID NOT NULL REFERENCES app_users(user_id) ON DELETE CASCADE,
    cryptocurrency_id BIGINT
        REFERENCES cryptocurrencies(cryptocurrency_id) ON DELETE CASCADE,
    alert_type      alert_type NOT NULL,
    title           VARCHAR(255) NOT NULL,
    message         TEXT NOT NULL,
    alert_data      JSONB NOT NULL DEFAULT '{}'::jsonb,
    triggered_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    read_at         TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_alert_events_user_unread
    ON alert_events(user_id, triggered_at DESC)
    WHERE read_at IS NULL;

-- =========================================================
-- 11. AUTOMATIC UPDATED_AT TRIGGER
-- =========================================================

CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_data_sources_updated_at ON data_sources;
CREATE TRIGGER trg_data_sources_updated_at
BEFORE UPDATE ON data_sources
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

DROP TRIGGER IF EXISTS trg_cryptocurrencies_updated_at ON cryptocurrencies;
CREATE TRIGGER trg_cryptocurrencies_updated_at
BEFORE UPDATE ON cryptocurrencies
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

DROP TRIGGER IF EXISTS trg_wallets_updated_at ON wallets;
CREATE TRIGGER trg_wallets_updated_at
BEFORE UPDATE ON wallets
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

DROP TRIGGER IF EXISTS trg_app_users_updated_at ON app_users;
CREATE TRIGGER trg_app_users_updated_at
BEFORE UPDATE ON app_users
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

DROP TRIGGER IF EXISTS trg_watchlists_updated_at ON watchlists;
CREATE TRIGGER trg_watchlists_updated_at
BEFORE UPDATE ON watchlists
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- =========================================================
-- 12. FRONT-END VIEWS
-- =========================================================

-- Latest market snapshot for each cryptocurrency.
CREATE OR REPLACE VIEW latest_market_data AS
SELECT DISTINCT ON (ms.cryptocurrency_id)
    ms.cryptocurrency_id,
    ms.price_usd,
    ms.market_cap_usd,
    ms.fully_diluted_valuation_usd,
    ms.volume_24h_usd,
    ms.price_change_1h_pct,
    ms.price_change_24h_pct,
    ms.price_change_7d_pct,
    ms.market_rank,
    ms.observed_at
FROM market_snapshots ms
ORDER BY ms.cryptocurrency_id, ms.observed_at DESC;

-- Latest risk assessment for each cryptocurrency.
CREATE OR REPLACE VIEW latest_risk_assessments AS
SELECT DISTINCT ON (ra.cryptocurrency_id)
    ra.risk_assessment_id,
    ra.cryptocurrency_id,
    ra.overall_risk_score,
    ra.risk_level,
    ra.confidence_score,
    ra.summary,
    ra.assessed_at
FROM risk_assessments ra
ORDER BY ra.cryptocurrency_id, ra.assessed_at DESC;

-- Dashboard view for the front end.
CREATE OR REPLACE VIEW cryptocurrency_dashboard AS
SELECT
    c.cryptocurrency_id,
    c.name,
    c.symbol,
    c.contract_address,
    c.logo_url,
    b.name AS blockchain_name,
    b.symbol AS blockchain_symbol,
    m.price_usd,
    m.market_cap_usd,
    m.volume_24h_usd,
    m.price_change_24h_pct,
    m.market_rank,
    r.overall_risk_score,
    COALESCE(r.risk_level, 'UNKNOWN'::risk_level) AS risk_level,
    r.confidence_score,
    r.summary AS risk_summary,
    m.observed_at AS market_data_updated_at,
    r.assessed_at AS risk_assessed_at
FROM cryptocurrencies c
LEFT JOIN blockchains b
    ON b.blockchain_id = c.blockchain_id
LEFT JOIN latest_market_data m
    ON m.cryptocurrency_id = c.cryptocurrency_id
LEFT JOIN latest_risk_assessments r
    ON r.cryptocurrency_id = c.cryptocurrency_id
WHERE c.is_active = TRUE;

-- Latest concentration data for each cryptocurrency.
CREATE OR REPLACE VIEW latest_concentration_data AS
SELECT DISTINCT ON (cs.cryptocurrency_id)
    cs.cryptocurrency_id,
    cs.holder_count,
    cs.top_1_pct,
    cs.top_5_pct,
    cs.top_10_pct,
    cs.top_20_pct,
    cs.developer_wallet_pct,
    cs.exchange_wallet_pct,
    cs.burn_wallet_pct,
    cs.observed_at
FROM concentration_snapshots cs
ORDER BY cs.cryptocurrency_id, cs.observed_at DESC;

-- =========================================================
-- 13. STARTER DATA
-- =========================================================

INSERT INTO data_sources (source_name, base_url, source_type)
VALUES
    ('CoinGecko', 'https://www.coingecko.com', 'MARKET_DATA'),
    ('Etherscan', 'https://etherscan.io', 'BLOCKCHAIN_EXPLORER'),
    ('BscScan', 'https://bscscan.com', 'BLOCKCHAIN_EXPLORER'),
    ('DexScreener', 'https://dexscreener.com', 'DEX_DATA'),
    ('GitHub', 'https://github.com', 'DEVELOPER_ACTIVITY')
ON CONFLICT (source_name) DO NOTHING;

INSERT INTO blockchains (name, symbol, chain_identifier, explorer_url, native_currency)
VALUES
    ('Ethereum', 'ETH', '1', 'https://etherscan.io', 'ETH'),
    ('BNB Smart Chain', 'BNB', '56', 'https://bscscan.com', 'BNB'),
    ('Solana', 'SOL', 'solana-mainnet', 'https://solscan.io', 'SOL'),
    ('Polygon', 'POL', '137', 'https://polygonscan.com', 'POL')
ON CONFLICT (name) DO NOTHING;

INSERT INTO risk_models (model_name, version, description, configuration)
VALUES (
    'NoRugs Core Risk Model',
    '1.0.0',
    'Weighted cryptocurrency scam and rug-pull risk model.',
    '{
        "wallet_concentration": 0.20,
        "liquidity": 0.20,
        "smart_contract": 0.20,
        "transaction_activity": 0.15,
        "developer_activity": 0.10,
        "market_stability": 0.10,
        "social_signals": 0.05
    }'::jsonb
)
ON CONFLICT (model_name, version) DO NOTHING;

COMMIT;
