import logging
import os
import time

import psycopg
from dotenv import load_dotenv
from psycopg.rows import dict_row

load_dotenv()

logger = logging.getLogger(__name__)

STARTING_TASKS = [
    {"title": "Learn FastAPI basics", "done": False},
    {"title": "Write API tests", "done": False},
    {"title": "Review Swagger docs", "done": True},
]


def get_database_url():
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL environment variable is required")
    return database_url


def get_connection():
    return psycopg.connect(get_database_url(), row_factory=dict_row)


def initialize_database(max_attempts=10, wait_seconds=2):
    last_error = None

    for attempt in range(1, max_attempts + 1):
        try:
            with get_connection() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        CREATE TABLE IF NOT EXISTS tasks (
                            id SERIAL PRIMARY KEY,
                            title TEXT NOT NULL,
                            done BOOLEAN NOT NULL DEFAULT FALSE
                        )
                        """
                    )
                    cursor.execute("SELECT COUNT(*) AS task_count FROM tasks")
                    task_count = cursor.fetchone()["task_count"]

                    if task_count == 0:
                        for task in STARTING_TASKS:
                            cursor.execute(
                                "INSERT INTO tasks (title, done) VALUES (%s, %s)",
                                (task["title"], task["done"]),
                            )

                connection.commit()
            return
        except psycopg.OperationalError as error:
            last_error = error
            logger.warning(
                "PostgreSQL is not ready yet (attempt %s/%s): %s",
                attempt,
                max_attempts,
                error,
            )
            if attempt < max_attempts:
                time.sleep(wait_seconds)

    raise RuntimeError("Could not connect to PostgreSQL after several attempts") from last_error
