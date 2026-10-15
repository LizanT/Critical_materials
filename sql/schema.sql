-- Critical Minerals Platform: database schema (PostgreSQL)
-- Reconstructs the database from scratch. Reflects the live database as of 2026-10-13.

CREATE TABLE IF NOT EXISTS minerals (
    mineral_id        SERIAL PRIMARY KEY,
    name              VARCHAR(100) NOT NULL UNIQUE,
    symbol            VARCHAR(20),
    category          VARCHAR(50),
    primary_uses      TEXT,
    on_usgs_2025_list BOOLEAN DEFAULT TRUE,
    csv_commodity     VARCHAR(100)
);

CREATE TABLE IF NOT EXISTS countries (
    country_id SERIAL PRIMARY KEY,
    name       VARCHAR(100) NOT NULL UNIQUE,
    iso_code   VARCHAR(3)
);

CREATE TABLE IF NOT EXISTS production (
    production_id SERIAL PRIMARY KEY,
    mineral_id    INTEGER NOT NULL REFERENCES minerals(mineral_id),
    country_id    INTEGER NOT NULL REFERENCES countries(country_id),
    year          INTEGER NOT NULL,
    tonnes        NUMERIC(15,2),
    source        VARCHAR(200),
    is_aggregated BOOLEAN DEFAULT FALSE,
    UNIQUE (mineral_id, country_id, year)
);

CREATE TABLE IF NOT EXISTS reserves (
    reserve_id    SERIAL PRIMARY KEY,
    mineral_id    INTEGER NOT NULL REFERENCES minerals(mineral_id),
    country_id    INTEGER NOT NULL REFERENCES countries(country_id),
    year          INTEGER NOT NULL,
    tonnes        NUMERIC(15,2),
    source        VARCHAR(200),
    is_aggregated BOOLEAN DEFAULT FALSE,
    UNIQUE (mineral_id, country_id, year)
);

CREATE TABLE IF NOT EXISTS prices (
    price_id      SERIAL PRIMARY KEY,
    mineral_id    INTEGER NOT NULL REFERENCES minerals(mineral_id),
    price_date    DATE NOT NULL,
    price_usd     NUMERIC(15,4),
    unit          VARCHAR(20),
    market_source VARCHAR(100),
    is_proxy      BOOLEAN DEFAULT FALSE,
    CONSTRAINT prices_mineral_date_unique UNIQUE (mineral_id, price_date)
);

-- KPI views -----------------------------------------------------------------

-- Herfindahl-Hirschman Index of production (sum of squared % shares; ~10,000 = one country dominates)
CREATE OR REPLACE VIEW hhi_production AS
WITH shares AS (
    SELECT mineral_id, year, country_id, tonnes,
           SUM(tonnes) OVER (PARTITION BY mineral_id, year) AS total_tonnes,
           (tonnes / SUM(tonnes) OVER (PARTITION BY mineral_id, year)) * 100 AS market_share_pct
    FROM production
    WHERE tonnes IS NOT NULL AND tonnes > 0
)
SELECT mineral_id, year,
       SUM(market_share_pct ^ 2) AS hhi,
       COUNT(DISTINCT country_id) AS num_producing_countries
FROM shares
GROUP BY mineral_id, year;

CREATE OR REPLACE VIEW hhi_reserves AS
WITH shares AS (
    SELECT mineral_id, year, country_id, tonnes,
           SUM(tonnes) OVER (PARTITION BY mineral_id, year) AS total_tonnes,
           (tonnes / SUM(tonnes) OVER (PARTITION BY mineral_id, year)) * 100 AS market_share_pct
    FROM reserves
    WHERE tonnes IS NOT NULL AND tonnes > 0
)
SELECT mineral_id, year,
       SUM(market_share_pct ^ 2) AS hhi,
       COUNT(DISTINCT country_id) AS num_reserve_countries
FROM shares
GROUP BY mineral_id, year;

-- Criticality score = 0.6 * production HHI + 0.4 * reserves HHI.
-- Minerals missing one side use only the available HHI (see has_*_data flags); not comparable with full scores.
CREATE OR REPLACE VIEW criticality_index AS
SELECT m.mineral_id, m.name AS mineral_name,
       p.hhi AS production_hhi, r.hhi AS reserves_hhi,
       p.num_producing_countries, r.num_reserve_countries,
       (p.hhi IS NOT NULL) AS has_production_data,
       (r.hhi IS NOT NULL) AS has_reserves_data,
       ROUND(CASE WHEN p.hhi IS NOT NULL AND r.hhi IS NOT NULL
                  THEN p.hhi * 0.6 + r.hhi * 0.4
                  ELSE COALESCE(p.hhi, r.hhi) END::numeric, 2) AS criticality_score
FROM minerals m
LEFT JOIN hhi_production p ON p.mineral_id = m.mineral_id
LEFT JOIN hhi_reserves  r ON r.mineral_id = m.mineral_id
WHERE p.hhi IS NOT NULL OR r.hhi IS NOT NULL;

-- Production value = tonnes * price. Excludes aggregated groups and magnesium (production/price basis mismatch).
CREATE OR REPLACE VIEW mining_value_score AS
SELECT p.mineral_id, m.name AS mineral_name, p.country_id, c.name AS country_name,
       p.year, p.tonnes, pr.price_usd,
       ROUND((p.tonnes * pr.price_usd)::numeric, 2) AS production_value_usd,
       p.is_aggregated
FROM production p
JOIN minerals m  ON m.mineral_id = p.mineral_id
JOIN countries c ON c.country_id = p.country_id
JOIN prices pr   ON pr.mineral_id = p.mineral_id
                AND EXTRACT(YEAR FROM pr.price_date) = p.year
WHERE pr.price_usd IS NOT NULL
  AND p.is_aggregated = FALSE
  AND m.name <> 'magnesium';
