"""Rutas del proyecto, independientes del directorio desde el que se ejecute."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORLD_DATA_CSV = ROOT / "data" / "raw" / "World_Data.csv"
SALIENT_DIR = ROOT / "data" / "raw" / "Salient_Commodity_Data_Release_Grouped_MCS_2025"
YEAR = 2024
