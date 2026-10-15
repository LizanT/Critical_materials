"""Carga a Postgres: TRUNCATE + INSERT de producción, reservas y precios en UNA transacción."""
import pandas as pd
from sqlalchemy import text


def _with_ids(df, minerals, countries=None):
    m = dict(zip(minerals["name"], minerals["mineral_id"]))
    out = df.copy()
    out["mineral_id"] = out["mineral_name"].map(m)
    assert out["mineral_id"].notna().all(), f"Minerales sin id: {sorted(out[out['mineral_id'].isna()]['mineral_name'].unique())}"
    if countries is not None:
        c = dict(zip(countries["name"], countries["country_id"]))
        out["country_id"] = out["country_name"].map(c)
        assert out["country_id"].notna().all(), f"Países sin id: {sorted(out[out['country_id'].isna()]['country_name'].unique())}"
    return out


def load_all(engine, production, reserves, prices):
    minerals = pd.read_sql("SELECT mineral_id, name FROM minerals", engine)
    countries = pd.read_sql("SELECT country_id, name FROM countries", engine)
    prod = _with_ids(production, minerals, countries)
    res = _with_ids(reserves, minerals, countries)
    pri = _with_ids(prices, minerals)

    with engine.begin() as conn:  # si algo falla, no se toca nada
        conn.execute(text("TRUNCATE production, reserves, prices RESTART IDENTITY"))
        prod[["mineral_id", "country_id", "year", "tonnes", "is_aggregated", "source"]] \
            .to_sql("production", conn, if_exists="append", index=False)
        res[["mineral_id", "country_id", "year", "tonnes", "is_aggregated", "source"]] \
            .to_sql("reserves", conn, if_exists="append", index=False)
        pri[["mineral_id", "price_date", "price_usd", "unit", "market_source", "is_proxy"]] \
            .to_sql("prices", conn, if_exists="append", index=False)
