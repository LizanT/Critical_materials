"""Pipeline completo. Por defecto solo valida (dry-run); `--load` escribe en Postgres.

    python -m etl.main          # valida
    python -m etl.main --load   # valida y carga
"""
import argparse

from etl.config import WORLD_DATA_CSV
from etl.prices import build_prices
from etl.transform import build_production, build_reserves, prepare_world_data


def run(load: bool = False):
    df = prepare_world_data(WORLD_DATA_CSV)
    production, reserves = build_production(df), build_reserves(df)
    prices = build_prices()
    print(f"production={len(production)} reserves={len(reserves)} prices={len(prices)}")

    # Comprobaciones de cordura (valores verificados a mano contra la fuente)
    t = production.query("mineral_name=='rhenium' and country_name=='Chile'")["tonnes"]
    assert len(t) == 1 and abs(t.iloc[0] - 29.0) < 1e-6, f"Renio Chile: {t.tolist()}"
    p = prices.query("price_date.astype('str')=='2024-01-01'").set_index("mineral_name")["price_usd"]
    assert p["manganese"] == 580, p["manganese"]
    assert p["chromium"] == 340, p["chromium"]
    assert not production.duplicated(["mineral_name", "country_name", "year"]).any()
    assert not reserves.duplicated(["mineral_name", "country_name", "year"]).any()
    print("Comprobaciones OK")

    if load:
        from etl.db import get_engine
        from etl.load import load_all
        load_all(get_engine(), production, reserves, prices)
        print("Carga completada")
    else:
        print("Dry-run: no se escribió nada (usa --load)")
    return production, reserves, prices


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--load", action="store_true")
    run(ap.parse_args().load)
