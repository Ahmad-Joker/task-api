from db import connect


TOTALS_SQL = """
SELECT
  COUNT(*) AS total_orders,
  ROUND(SUM(amount), 2) AS total_revenue,
  ROUND(AVG(amount), 2) AS average_order_value
FROM orders
"""

TOP_PRODUCTS_SQL = """
SELECT
  product,
  COUNT(*) AS order_count,
  ROUND(SUM(amount), 2) AS revenue
FROM orders
GROUP BY product
ORDER BY revenue DESC
LIMIT 5
"""

ORDERS_PER_DAY_SQL = """
SELECT
  created_at AS day,
  COUNT(*) AS order_count,
  ROUND(SUM(amount), 2) AS revenue
FROM orders
WHERE created_at >= date((SELECT MAX(created_at) FROM orders), '-6 days')
GROUP BY created_at
ORDER BY created_at ASC
"""

ALL_ORDERS_SQL = """
SELECT id, customer, product, amount, created_at
FROM orders
ORDER BY created_at DESC, id ASC
"""


def rows_to_dicts(rows):
    return [dict(row) for row in rows]


def get_report_data():
    with connect() as connection:
        totals = dict(connection.execute(TOTALS_SQL).fetchone())
        top_products = rows_to_dicts(connection.execute(TOP_PRODUCTS_SQL).fetchall())
        orders_per_day = rows_to_dicts(connection.execute(ORDERS_PER_DAY_SQL).fetchall())
        all_orders = rows_to_dicts(connection.execute(ALL_ORDERS_SQL).fetchall())

    return {
        "totals": totals,
        "top_products": top_products,
        "orders_per_day": orders_per_day,
        "orders": all_orders,
    }
