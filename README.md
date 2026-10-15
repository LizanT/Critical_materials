# Critical Minerals Platform

Data analysis of the U.S. critical minerals list (USGS 2025): who produces them, who holds the reserves, what they are worth, and how concentrated the supply is.

```
USGS MCS 2025 (CSV) → Python ETL → PostgreSQL → SQL views (KPIs) → Power BI
```

## Key metrics

All metrics are SQL views in [`sql/schema.sql`](sql/schema.sql), for 2024.

| View | What it measures |
|---|---|
| `hhi_production`, `hhi_reserves` | Herfindahl-Hirschman Index of supply concentration (sum of squared market shares; ~10,000 = a single country dominates) |
| `criticality_index` | `0.6 × production HHI + 0.4 × reserves HHI` per mineral |
| `mining_value_score` | Production value per mineral and country (`tonnes × USD/tonne`) |

## Data

Source: USGS, *Mineral Commodity Summaries 2025, Data Release* (ver. 2.0), DOI [10.5066/P13XCP3R](https://doi.org/10.5066/P13XCP3R). Public domain. Raw files live in [`data/raw/`](data/raw/).

- 55 of the 60 critical minerals appear in the USGS world data.
- Output: 566 production rows, 472 reserves rows, 271 price rows.

## Project structure

```
data/raw/      USGS source files
docs/          methodology.md: cleaning, unit normalization, pricing decisions, limitations
etl/           extract-transform-load pipeline (only code that writes to the database)
notebooks/     exploration and validation only; they never write to the database
sql/           schema.sql: tables and KPI views
```

## Setup

1. Create a PostgreSQL database and run [`sql/schema.sql`](sql/schema.sql).
2. Copy `.env.example` to `.env` and fill in your connection details.
3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Run the pipeline from the project root:

   ```bash
   python -m etl.main          # dry run: builds and validates, writes nothing
   python -m etl.main --load   # validates and loads into PostgreSQL
   ```

   Expected dry-run output: `production=566 reserves=472 prices=271` and `Comprobaciones OK`.

> The `minerals` and `countries` reference tables are loaded once, separately; the ETL only fills `production`, `reserves` and `prices`.

## Limitations

Full detail in [`docs/methodology.md`](docs/methodology.md). The main ones:

- Rare earths, platinum-group metals and Zr+Hf are published by USGS as a single group value, so their members share the same figure and are flagged `is_aggregated`.
- 8 rare earth prices are proxies (`is_proxy`), based on the mischmetal price.
- Production and price units were audited for chromium, manganese and tungsten only. Known unresolved mismatches: vanadium, tantalum, potash, beryllium, silicon.
- `Other Countries` is excluded, so HHI may be slightly overestimated.
- Prices are annual USD averages, partly U.S. import unit values.

## Roadmap

Power BI dashboard, a redefined accessibility index, price-basis audit for the remaining minerals, an API and a web front end.
