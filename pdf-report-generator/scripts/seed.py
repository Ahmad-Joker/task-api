from datetime import date, timedelta
from pathlib import Path
import random
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from db import connect, initialize_database


CUSTOMERS = ["Acme Co", "Northwind", "Bluebird Labs", "Cairo Studio", "Atlas Goods", "Riverline"]
PRODUCTS = ["Starter Plan", "Pro Plan", "Audit Pack", "Priority Support", "Data Export", "Team Seats"]


def seed_orders():
    initialize_database()
    random.seed(20260822)
    today = date.today()

    with connect() as connection:
        connection.execute("DELETE FROM orders")
        for index in range(200):
            connection.execute(
                """
                INSERT INTO orders (customer, product, amount, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (
                    random.choice(CUSTOMERS),
                    random.choice(PRODUCTS),
                    round(random.uniform(5, 200), 2),
                    (today - timedelta(days=random.randint(0, 29))).isoformat(),
                ),
            )
        connection.commit()


if __name__ == "__main__":
    seed_orders()
    with connect() as connection:
        count = connection.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
    print(f"orders={count}")
