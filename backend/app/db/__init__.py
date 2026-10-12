"""
Database layer for SQLite connections and schema initialization.
"""
from app.db.connection import get_connection, DB_PATH, DB_DIR
from app.db.init_db import init_db

__all__ = ["get_connection", "init_db", "DB_PATH", "DB_DIR"]
