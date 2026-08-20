# etl/db.py
import os
from urllib.parse import quote_plus
from dotenv import load_dotenv
from sqlalchemy import create_engine

def get_engine():
    load_dotenv('../.env')
    password = quote_plus(os.getenv('DB_PASSWORD'))
    return create_engine(
        f"postgresql://{os.getenv('DB_USER')}:{password}"
        f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
    )