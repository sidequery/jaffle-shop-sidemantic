# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "sidemantic[lookml,malloy]>=0.8.2",
#     "polars",
#     "pyarrow",
# ]
# ///

# %% [markdown]
# # Jaffle Shop: Multi-Format Semantic Layer Demo
#
# 5 models defined in 5 different semantic layer formats, loaded into a single
# unified graph by [sidemantic](https://github.com/sidequery/sidemantic).
#
# | Model | Format | Source |
# |-------|--------|--------|
# | orders | MetricFlow | `models/metricflow/orders.yml` |
# | order_items | Cube | `models/cube/order_items.yml` |
# | customers | LookML | `models/lookml/customers.lkml` |
# | locations | Malloy | `models/malloy/locations.malloy` |
# | products | OSI | `models/osi/products.yml` |

# %%
from pathlib import Path
from sidemantic import SemanticLayer, load_from_directory
import polars as pl

db_path = Path("jaffle_shop.duckdb").resolve()
layer = SemanticLayer(connection=f"duckdb:///{db_path}")
load_from_directory(layer, "models/")

print(f"Models: {layer.list_models()}")
print(f"Metrics: {layer.list_metrics()}")

# %% [markdown]
# ---
# ## Sidemantic SQL: `layer.sql()`
#
# SQL with `model.field` references. Joins are inferred from relationships,
# GROUP BY is derived from dimensions. No explicit aggregation: the semantic
# layer handles it.

# %% [markdown]
# ### 1. Revenue by product

# %%
layer.sql("""
    SELECT
        order_items.product_name,
        order_items.revenue,
        order_items.item_count,
        order_items.supply_cost
    FROM order_items
    ORDER BY order_items.revenue DESC
""").pl()

# %% [markdown]
# ### 2. Food vs drink revenue by product

# %%
layer.sql("""
    SELECT
        order_items.product_name,
        order_items.revenue,
        order_items.food_revenue,
        order_items.drink_revenue
    FROM order_items
    ORDER BY order_items.revenue DESC
""").pl()

# %% [markdown]
# ### 3. Order type analysis

# %%
layer.sql("""
    SELECT
        orders.is_food_order,
        orders.order_count,
        orders.order_total,
        orders.food_order_count,
        orders.drink_order_count
    FROM orders
""").pl()

# %% [markdown]
# ### 4. Customer lifetime value by type

# %%
layer.sql("""
    SELECT
        customers.customer_type,
        customers.customer_count,
        customers.lifetime_spend,
        customers.total_lifetime_orders
    FROM customers
""").pl()

# %% [markdown]
# ### 5. Location performance

# %%
layer.sql("""
    SELECT
        locations.location_name,
        locations.tax_rate,
        locations.location_count
    FROM locations
    ORDER BY locations.tax_rate DESC
""").pl()

# %% [markdown]
# ### 6. Monthly revenue trends

# %%
layer.sql("""
    SELECT orders.ordered_at, orders.order_total, orders.order_count
    FROM orders
    ORDER BY orders.ordered_at
""").pl()

# %% [markdown]
# ### 7. Monthly orders with new customer breakdown

# %%
layer.sql("""
    SELECT
        orders.ordered_at,
        orders.order_total,
        orders.order_count,
        orders.new_customer_order_count
    FROM orders
    ORDER BY orders.ordered_at
""").pl()

# %% [markdown]
# ### 8. Cross-model: orders by customer type (auto-join MetricFlow + LookML)

# %%
layer.sql("""
    SELECT
        customers.customer_type,
        orders.order_count,
        orders.order_total,
        orders.food_order_count,
        orders.drink_order_count
    FROM orders
""").pl()

# %% [markdown]
# ---
# ## Yardstick SQL: SEMANTIC SELECT with AGGREGATE() and AT
#
# Sidemantic supports Julian Hyde's [Measures in SQL](https://arxiv.org/abs/2307.15107)
# syntax. `AGGREGATE()` wraps a measure and applies its defined aggregation in the
# current grouping context. `AT (ALL)` overrides grouping to compute across all rows,
# enabling percent-of-total without window functions.

# %% [markdown]
# ### 9. Product revenue with percent of total

# %%
layer.sql("""
    SEMANTIC SELECT
        order_items.product_name,
        AGGREGATE(order_items.revenue) AS revenue,
        100.0 * AGGREGATE(order_items.revenue) / AGGREGATE(order_items.revenue) AT (ALL) AS pct_of_total,
        AGGREGATE(order_items.item_count) AS units_sold
    FROM order_items
    ORDER BY revenue DESC
""").pl()

# %% [markdown]
# ### 10. Gross profit by product

# %%
layer.sql("""
    SEMANTIC SELECT
        order_items.product_name,
        AGGREGATE(order_items.revenue) AS revenue,
        AGGREGATE(order_items.supply_cost) AS cost,
        AGGREGATE(order_items.revenue) - AGGREGATE(order_items.supply_cost) AS gross_profit,
        100.0 * (AGGREGATE(order_items.revenue) - AGGREGATE(order_items.supply_cost)) / AGGREGATE(order_items.revenue) AS margin_pct
    FROM order_items
    ORDER BY gross_profit DESC
""").pl()

# %% [markdown]
# ### 11. Order types with AT (ALL) percent

# %%
layer.sql("""
    SEMANTIC SELECT
        orders.is_food_order,
        AGGREGATE(orders.order_count) AS orders,
        AGGREGATE(orders.order_total) AS revenue,
        100.0 * AGGREGATE(orders.order_total) / AGGREGATE(orders.order_total) AT (ALL) AS pct_of_revenue
    FROM orders
    ORDER BY revenue DESC
""").pl()

# %% [markdown]
# ### 12. Monthly revenue with percent of annual total

# %%
layer.sql("""
    SEMANTIC SELECT
        orders.ordered_at,
        AGGREGATE(orders.order_total) AS monthly_revenue,
        AGGREGATE(orders.order_count) AS monthly_orders,
        100.0 * AGGREGATE(orders.order_total) / AGGREGATE(orders.order_total) AT (ALL) AS pct_of_annual
    FROM orders
    ORDER BY orders.ordered_at
""").pl()

# %% [markdown]
# ---
# ## Python API: `layer.query()`
#
# Structured queries using `metrics`, `dimensions`, `filters`, `segments`,
# and `order_by` parameters.

# %% [markdown]
# ### 13. Daily revenue and order count

# %%
layer.query(
    metrics=["orders.order_total", "orders.order_count"],
    dimensions=["orders.ordered_at"],
    order_by=["orders.ordered_at"],
).pl()

# %% [markdown]
# ### 14. Monthly new customer acquisition

# %%
layer.query(
    metrics=["orders.order_count", "orders.new_customer_order_count"],
    dimensions=["orders.ordered_at__month"],
    order_by=["orders.ordered_at__month"],
).pl()

# %% [markdown]
# ### 15. Cross-model: order metrics by customer type

# %%
layer.query(
    metrics=["orders.order_count", "orders.order_total", "orders.food_order_count", "orders.drink_order_count"],
    dimensions=["customers.customer_type"],
).pl()
