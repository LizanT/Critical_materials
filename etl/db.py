"""Conexión a Postgres. El .env se busca siempre en la raíz del proyecto."""
import os
from urllib.parse import quote_plus

from dotenv import load_dotenv
from sqlalchemy import create_engine

from etl.config import ROOT

REQUIRED = ("DB_USER", "DB_PASSWORD", "DB_HOST", "DB_PORT", "DB_NAME")


def get_engine():
    env_path = ROOT / ".env"
    load_dotenv(env_path, override=True)
    missing = [k for k in REQUIRED if not os.getenv(k)]
    if missing:
        raise RuntimeError(
            f"Faltan variables en {env_path} (¿archivo vacío o sin guardar?): {missing}"
        )
    password = quote_plus(os.getenv("DB_PASSWORD"))
    return create_engine(
                f"postgresql+psycopg2://{os.getenv('DB_USER')}:{password}"
        f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
    )
