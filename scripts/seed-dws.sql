-- scripts/seed-dws.sql
-- Seed DWS schema + sample queries para AYCO demo
-- Ejecutar: PGPASSWORD=$DWS_ADMIN_PASSWORD psql -h $DWS_ENDPOINT -U ayco_admin -d ayco -f seed-dws.sql

-- ─── Schema (si no existe) ──────────────────────────
CREATE SCHEMA IF NOT EXISTS ods;
CREATE SCHEMA IF NOT EXISTS dw;
CREATE SCHEMA IF NOT EXISTS dm;
CREATE SCHEMA IF NOT EXISTS rpt;

-- ─── ODS: Tablas raw ────────────────────────────────
CREATE TABLE IF NOT EXISTS ods.vendors (
    vendor_id           VARCHAR(10) PRIMARY KEY,
    name                VARCHAR(200),
    sector              VARCHAR(50),
    state               VARCHAR(10),
    city                VARCHAR(100),
    risk_level          VARCHAR(20),
    risk_score          NUMERIC(4,1),
    annual_revenue_mxn  NUMERIC(15,2),
    debt_ratio          NUMERIC(3,2),
    contract_count      INT,
    employee_count      INT,
    ingested_at         TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ods.customers (
    customer_id         VARCHAR(10) PRIMARY KEY,
    name                VARCHAR(200),
    kyc_level           VARCHAR(10),
    monthly_limit_mxn   INT,
    risk_score          NUMERIC(4,1),
    state               VARCHAR(10),
    city                VARCHAR(100),
    account_age_days    INT,
    ingested_at         TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ods.transactions (
    tx_id       VARCHAR(12) PRIMARY KEY,
    vendor_id   VARCHAR(10),
    customer_id VARCHAR(10),
    amount_mxn  NUMERIC(15,2),
    anomaly_type VARCHAR(20),
    timestamp   TIMESTAMP,
    city_from   VARCHAR(100),
    city_to     VARCHAR(100),
    ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ─── DW: Dimensiones ────────────────────────────────
CREATE TABLE IF NOT EXISTS dw.dim_vendor (
    vendor_key   SERIAL PRIMARY KEY,
    vendor_id    VARCHAR(10) UNIQUE,
    name         VARCHAR(200),
    sector       VARCHAR(50),
    state        VARCHAR(10),
    city         VARCHAR(100),
    risk_level   VARCHAR(20),
    risk_score   NUMERIC(4,1)
);

CREATE TABLE IF NOT EXISTS dw.dim_customer (
    customer_key SERIAL PRIMARY KEY,
    customer_id  VARCHAR(10) UNIQUE,
    name         VARCHAR(200),
    kyc_level    VARCHAR(10),
    monthly_limit_mxn INT,
    risk_score   NUMERIC(4,1)
);

CREATE TABLE IF NOT EXISTS dw.fact_transaction (
    tx_key       SERIAL PRIMARY KEY,
    tx_id        VARCHAR(12),
    vendor_key   INT REFERENCES dw.dim_vendor(vendor_key),
    customer_key INT REFERENCES dw.dim_customer(customer_key),
    amount_mxn   NUMERIC(15,2),
    anomaly_type VARCHAR(20),
    timestamp    TIMESTAMP
);

-- ─── DM: Vistas materializadas para reportes ────────
CREATE MATERIALIZED VIEW IF NOT EXISTS dm.vendor_risk_summary AS
SELECT
    risk_level,
    COUNT(*) AS vendor_count,
    ROUND(AVG(risk_score), 1) AS avg_score,
    SUM(annual_revenue_mxn) AS total_exposure
FROM ods.vendors
GROUP BY risk_level;

CREATE MATERIALIZED VIEW IF NOT EXISTS dm.city_risk AS
SELECT
    city,
    COUNT(*) AS vendor_count,
    COUNT(CASE WHEN risk_level IN ('Alto', 'Crítico') THEN 1 END) AS high_risk_count
FROM ods.vendors
GROUP BY city;

CREATE MATERIALIZED VIEW IF NOT EXISTS dm.anomaly_summary AS
SELECT
    anomaly_type,
    COUNT(*) AS count,
    ROUND(AVG(amount_mxn), 2) AS avg_amount,
    SUM(amount_mxn) AS total_amount
FROM ods.transactions
WHERE anomaly_type != 'normal'
GROUP BY anomaly_type;

-- ─── Contract Risk Results (used by DataArts + DataService) ─────
CREATE TABLE IF NOT EXISTS risk_results (
    contract_number    VARCHAR(50) PRIMARY KEY,
    vendor_name        VARCHAR(200),
    monto_total        NUMERIC(15,2),
    plazo_dias         INT,
    penalizacion_pct   NUMERIC(5,2),
    garantia_pct       NUMERIC(5,2),
    risk_score         NUMERIC(5,2),
    risk_level         VARCHAR(20) CHECK (risk_level IN ('BAJO','MEDIO','ALTO','CRITICO')),
    alertas            TEXT,
    recomendaciones    TEXT,
    resumen            TEXT,
    llm_provider       VARCHAR(50),
    analyzed_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_risk_results_level ON risk_results(risk_level);
CREATE INDEX IF NOT EXISTS idx_risk_results_score ON risk_results(risk_score DESC);
CREATE INDEX IF NOT EXISTS idx_risk_results_vendor ON risk_results(vendor_name);

-- ─── RPT: Queries de reportes listas ─────────────────
-- (estas se corren en live durante el demo)

-- Reporte 1: Top vendors por riesgo
SELECT vendor_id, name, sector, risk_level, risk_score, annual_revenue_mxn
FROM ods.vendors
WHERE risk_level IN ('Alto', 'Crítico')
ORDER BY risk_score DESC
LIMIT 10;

-- Reporte 2: Exposición total por nivel de riesgo
SELECT * FROM dm.vendor_risk_summary;

-- Reporte 3: Anomalías CNBV detectadas
SELECT * FROM dm.anomaly_summary;

-- Reporte 4: Ciudades con más vendors de alto riesgo
SELECT * FROM dm.city_risk ORDER BY high_risk_count DESC;
