"""World Data (USGS MCS 2025) -> producción y reservas en toneladas métricas."""
import re

import pandas as pd

from etl.config import YEAR
from etl.mappings import csv_to_criticals

UNIT_FACTOR = {"metric tons": 1, "thousand metric tons": 1000, "kilograms": 0.001}


def clean_country(country: str) -> str:
    if "Kinshasa" in country:
        return "Democratic Republic of the Congo"
    if "Brazzaville" in country:
        return "Republic of the Congo"
    country = country.replace("\xa0", " ")
    country = re.sub(r"\s*\(.*?\)", "", country)
    return country.strip()


def prepare_world_data(path) -> pd.DataFrame:
    """Carga el CSV, limpia y deja solo commodities críticos, países reales y toneladas."""
    df = pd.read_csv(path)
    df.columns = df.columns.str.replace(" ", "", regex=False)
    df["COMMODITY"] = df["COMMODITY"].str.strip().replace({"Gemanium": "Germanium"})
    df["UNIT_MEAS"] = df["UNIT_MEAS"].str.strip()
    df["RESERVES_2024_clean"] = pd.to_numeric(
        df["RESERVES_2024"].astype(str).str.replace(">", "", regex=False)
        .str.replace(",", "", regex=False).str.strip(),
        errors="coerce",
    )

    mask_total = df["COUNTRY"].str.contains("World total|Other Countries", case=False, na=False)
    df = df[~mask_total].copy()
    df["COUNTRY_CLEAN"] = df["COUNTRY"].apply(clean_country)
    df = df[df["COUNTRY_CLEAN"] != "United States and Canada"]

    df = df[df["COMMODITY"].isin(csv_to_criticals.keys())].copy()
    df.loc[
        (df["COMMODITY"] == "Titanium Mineral Concentrates") & df["UNIT_MEAS"].isna(), "UNIT_MEAS"
    ] = "metric tons"
    df["factor"] = df["UNIT_MEAS"].map(UNIT_FACTOR)
    bad = df[df["factor"].isna()][["COMMODITY", "UNIT_MEAS"]]
    assert bad.empty, f"Unidad no reconocida:\n{bad}"
    return df


def expand_to_criticals(df_grouped: pd.DataFrame, value_col: str) -> pd.DataFrame:
    """Reparte cada commodity entre los minerales críticos que representa y fusiona duplicados."""
    rows = []
    for _, r in df_grouped.iterrows():
        criticals = csv_to_criticals[r["COMMODITY"]]
        for mineral in criticals:
            rows.append({
                "mineral_name": mineral,
                "country_name": r["COUNTRY_CLEAN"],
                "year": YEAR,
                "tonnes": r[value_col],
                "is_aggregated": len(criticals) > 1,
                "source": "USGS MCS 2025",
            })
    out = pd.DataFrame(rows)
    # Dos commodities del CSV pueden apuntar al mismo crítico (magnesio, titanio): se suman
    return out.groupby(["mineral_name", "country_name", "year"], as_index=False).agg(
        {"tonnes": "sum", "is_aggregated": "any", "source": "first"}
    )


def build_production(df: pd.DataFrame) -> pd.DataFrame:
    prod = df[df["PROD_EST_2024"].notna()].copy()
    prod = prod[~((prod["COMMODITY"] == "Copper") & (prod["TYPE"] == "Refinery production, copper"))]
    prod["tonnes"] = prod["PROD_EST_2024"] * prod["factor"]
    # Suma sub-tipos (PGM: Pt + Pd; silicio: ferrosilicio + metal; titanio: ilmenita + rutilo)
    prod = prod.groupby(["COMMODITY", "COUNTRY_CLEAN"], as_index=False).agg({"tonnes": "sum"})
    return expand_to_criticals(prod, "tonnes")


def build_reserves(df: pd.DataFrame) -> pd.DataFrame:
    res = df[df["RESERVES_2024_clean"].notna()].copy()
    res = res[~((res["COMMODITY"] == "Potash") & (res["TYPE"] == "Reserves, recoverable ore"))]
    res["tonnes"] = res["RESERVES_2024_clean"] * res["factor"]
    res = res.groupby(["COMMODITY", "COUNTRY_CLEAN"], as_index=False).agg({"tonnes": "sum"})
    return expand_to_criticals(res, "tonnes")
