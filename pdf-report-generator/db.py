from pathlib import Path
import sqlite3


BASE_DIR = Path(__file__).resolve().parent
DATABASE_PATH = BASE_DIR / "report.db"
REPORTS_DIR = BASE_DIR / "reports"


def connect():
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database():
    with connect() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer TEXT NOT NULL,
                product TEXT NOT NULL,
                amount REAL NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                path TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        connection.commit()
