# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "duckdb",
# ]
# ///
"""Build jaffle_shop.duckdb from the jaffle-shop seed CSVs.

Reproduces the dbt staging + mart transforms as plain SQL so
you don't need dbt installed. Run once before the demo:

    uv run setup.py
"""

import duckdb
from pathlib import Path

DB_PATH = Path("jaffle_shop.duckdb")
SEED_DIR = Path("jaffle-shop/seeds/jaffle-data")

if DB_PATH.exists():
    DB_PATH.unlink()
    print(f"Removed existing {DB_PATH}")

conn = duckdb.connect(str(DB_PATH))

# -- Load raw seeds -----------------------------------------------------------

for csv in sorted(SEED_DIR.glob("*.csv")):
    table = csv.stem  # raw_customers, raw_items, etc.
    conn.execute(f"CREATE TABLE {table} AS SELECT * FROM read_csv_auto('{csv}')")
    count = conn.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
    print(f"  {table}: {count:,} rows")

# -- Staging ------------------------------------------------------------------

conn.execute("""
    CREATE TABLE stg_customers AS
    SELECT id AS customer_id, name AS customer_name
    FROM raw_customers
""")

conn.execute("""
    CREATE TABLE stg_locations AS
    SELECT id AS location_id, name AS location_name, tax_rate,
           DATE_TRUNC('day', opened_at) AS opened_date
    FROM raw_stores
""")

conn.execute("""
    CREATE TABLE stg_products AS
    SELECT
        sku AS product_id,
        name AS product_name,
        type AS product_type,
        description AS product_description,
        price / 100.0 AS product_price,
        COALESCE(type = 'jaffle', false) AS is_food_item,
        COALESCE(type = 'beverage', false) AS is_drink_item
    FROM raw_products
""")

conn.execute("""
    CREATE TABLE stg_supplies AS
    SELECT
        md5(CAST(id AS VARCHAR) || '-' || CAST(sku AS VARCHAR)) AS supply_uuid,
        id AS supply_id,
        sku AS product_id,
        name AS supply_name,
        cost / 100.0 AS supply_cost,
        perishable AS is_perishable_supply
    FROM raw_supplies
""")

conn.execute("""
    CREATE TABLE stg_orders AS
    SELECT
        id AS order_id,
        store_id AS location_id,
        customer AS customer_id,
        subtotal AS subtotal_cents,
        tax_paid AS tax_paid_cents,
        order_total AS order_total_cents,
        subtotal / 100.0 AS subtotal,
        tax_paid / 100.0 AS tax_paid,
        order_total / 100.0 AS order_total,
        DATE_TRUNC('day', ordered_at) AS ordered_at
    FROM raw_orders
""")

conn.execute("""
    CREATE TABLE stg_order_items AS
    SELECT id AS order_item_id, order_id, sku AS product_id
    FROM raw_items
""")

# -- Marts --------------------------------------------------------------------

conn.execute("""
    CREATE TABLE supplies AS SELECT * FROM stg_supplies
""")

conn.execute("""
    CREATE TABLE products AS SELECT * FROM stg_products
""")

conn.execute("""
    CREATE TABLE locations AS SELECT * FROM stg_locations
""")

# order_items mart: join stg_order_items with orders, products, supplies
conn.execute("""
    CREATE TABLE order_items AS
    WITH order_supplies_summary AS (
        SELECT product_id, SUM(supply_cost) AS supply_cost
        FROM stg_supplies
        GROUP BY 1
    )
    SELECT
        oi.*,
        o.ordered_at,
        p.product_name,
        p.product_price,
        p.is_food_item,
        p.is_drink_item,
        oss.supply_cost
    FROM stg_order_items oi
    LEFT JOIN stg_orders o ON oi.order_id = o.order_id
    LEFT JOIN stg_products p ON oi.product_id = p.product_id
    LEFT JOIN order_supplies_summary oss ON oi.product_id = oss.product_id
""")

# orders mart: join stg_orders with order_items summary
conn.execute("""
    CREATE TABLE orders AS
    WITH order_items_summary AS (
        SELECT
            order_id,
            SUM(supply_cost) AS order_cost,
            SUM(product_price) AS order_items_subtotal,
            COUNT(order_item_id) AS count_order_items,
            SUM(CASE WHEN is_food_item THEN 1 ELSE 0 END) AS count_food_items,
            SUM(CASE WHEN is_drink_item THEN 1 ELSE 0 END) AS count_drink_items
        FROM order_items
        GROUP BY 1
    ),
    compute_booleans AS (
        SELECT
            o.*,
            ois.order_cost,
            ois.order_items_subtotal,
            ois.count_food_items,
            ois.count_drink_items,
            ois.count_order_items,
            ois.count_food_items > 0 AS is_food_order,
            ois.count_drink_items > 0 AS is_drink_order
        FROM stg_orders o
        LEFT JOIN order_items_summary ois ON o.order_id = ois.order_id
    )
    SELECT *,
        ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY ordered_at ASC) AS customer_order_number
    FROM compute_booleans
""")

# customers mart: join stg_customers with orders summary
conn.execute("""
    CREATE TABLE customers AS
    WITH customer_orders_summary AS (
        SELECT
            customer_id,
            COUNT(DISTINCT order_id) AS count_lifetime_orders,
            COUNT(DISTINCT order_id) > 1 AS is_repeat_buyer,
            MIN(ordered_at) AS first_ordered_at,
            MAX(ordered_at) AS last_ordered_at,
            SUM(subtotal) AS lifetime_spend_pretax,
            SUM(tax_paid) AS lifetime_tax_paid,
            SUM(order_total) AS lifetime_spend
        FROM orders
        GROUP BY 1
    )
    SELECT
        c.*,
        cos.count_lifetime_orders,
        cos.first_ordered_at,
        cos.last_ordered_at,
        cos.lifetime_spend_pretax,
        cos.lifetime_tax_paid,
        cos.lifetime_spend,
        CASE WHEN cos.is_repeat_buyer THEN 'returning' ELSE 'new' END AS customer_type
    FROM stg_customers c
    LEFT JOIN customer_orders_summary cos ON c.customer_id = cos.customer_id
""")

# metricflow time spine
conn.execute("""
    CREATE TABLE metricflow_time_spine AS
    SELECT UNNEST(generate_series(DATE '2024-01-01', DATE '2026-12-31', INTERVAL 1 DAY))::DATE AS date_day
""")

conn.close()

# -- Summary ------------------------------------------------------------------

conn = duckdb.connect(str(DB_PATH), read_only=True)
tables = conn.execute("""
    SELECT table_name, estimated_size
    FROM duckdb_tables()
    WHERE schema_name = 'main'
    ORDER BY table_name
""").fetchall()

print(f"\nBuilt {DB_PATH} with {len(tables)} tables:")
for name, size in tables:
    count = conn.execute(f"SELECT count(*) FROM {name}").fetchone()[0]
    print(f"  {name}: {count:,} rows")

conn.close()
