import sqlite3
import os
from app.core.config import settings

DB_DIR = str(settings.DATA_DIR)
DB_PATH = str(settings.DB_PATH)

def get_connection() -> sqlite3.Connection:
    """Returns a SQLite connection with Row factory configured."""
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn
