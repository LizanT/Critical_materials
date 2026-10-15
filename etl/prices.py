"""Salient Commodity Data -> precios anuales en USD por tonelada métrica."""
import pandas as pd

from etl.config import SALIENT_DIR
from etl.price_mapping import MTU_GRADE, PRICE_MAPPING, PROXY_MINERALS


def get_unit_factor(col: str):
    """Factor para pasar el precio de la columna a USD/tonelada métrica (según sufijo)."""
    if col.endswith("_dt") or col.endswith("_t") or "dt." in col:
        return 1
    if col.endswith("_dlb"):
        return 2204.62
    if col.endswith("_ctslb"):
        return 2204.62 / 100
    if col.endswith("_dkg"):
        return 1000
    if col.endswith("_dto") or col.endswith("_dtoz"):
        return 32150.7
    if col.endswith("_dg"):
        return 1_000_000
    return None


def build_prices(salient_dir=SALIENT_DIR) -> pd.DataFrame:
    rows = []
    for mineral, (fname, cols, how) in PRICE_MAPPING.items():
        df = pd.read_csv(salient_dir / fname)
        series = []
        for c in cols:
            factor = get_unit_factor(c)
            assert factor is not None, f"Sufijo de unidad desconocido: {c} ({mineral})"
            s = pd.to_numeric(df[c], errors="coerce") * factor
            series.append(s)
        vals = pd.concat(series, axis=1)
        price = vals.mean(axis=1) if how == "mean" else vals.iloc[:, 0]
        price = price * MTU_GRADE.get(mineral, 1)
        for year, p in zip(df["Year"], price):
            if pd.notna(p):
                rows.append({
                    "mineral_name": mineral,
                    "price_date": pd.Timestamp(int(year), 1, 1).date(),
                    "price_usd": round(float(p), 2),
                    "unit": "USD/tonne",
                    "market_source": "USGS MCS 2025 Salient",
                    "is_proxy": mineral in PROXY_MINERALS,
                })
    return pd.DataFrame(rows)
