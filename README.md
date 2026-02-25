# Jaffle Shop Semantic Layer

A multi-format semantic layer built on top of the [dbt jaffle shop](https://github.com/dbt-labs/jaffle-shop) project, using [sidemantic](https://github.com/sidequery/sidemantic) for metric definitions and measure-aware SQL querying.

## What's here

5 models, each defined in a different semantic layer format. Sidemantic loads them all into a single unified graph:

| Model | Format | Path |
|-------|--------|------|
| orders | MetricFlow | `models/metricflow/orders.yml` |
| order_items | Cube | `models/cube/order_items.yml` |
| customers | LookML | `models/lookml/customers.lkml` |
| locations | Malloy | `models/malloy/locations.malloy` |
| products | OSI | `models/osi/products.yml` |

## Data overview

| Table | Rows | Description |
|-------|------|-------------|
| orders | 61,948 | One row per order, with totals and flags |
| order_items | 90,900 | Line items with product prices and supply costs |
| customers | 935 | Customer dimension with lifetime aggregates |
| products | 10 | Product catalog (5 food, 5 drink) |
| locations | 6 | Store locations with tax rates |
| supplies | 65 | Supply costs per product/store |

## Models

```bash
# Validate all models (loads from all 5 formats)
sidemantic validate models/ --verbose

# Model summary
sidemantic info models/

# Query (auto-joins across models based on relationships)
sidemantic query "SELECT orders.order_count, orders.order_total, customers.customer_type FROM orders"

# See generated SQL without executing
sidemantic query --dry-run \
  "SELECT order_items.revenue, order_items.supply_cost FROM order_items"
```

### orders (MetricFlow)

`models/metricflow/orders.yml` uses dbt Semantic Layer (MetricFlow) format with `semantic_models:`, `entities:`, `dimensions:`, and `measures:`. 4 dimensions, 9 measures (including filtered measures via `meta.filters`), 2 relationships via foreign entities (customers, locations), 3 segments. Also contains graph-level metrics: average_order_value, gross_profit, food_revenue_pct, drink_revenue_pct, profit_margin, cumulative_revenue.

### order_items (Cube)

`models/cube/order_items.yml` uses Cube.js YAML syntax with `${CUBE}` self-references and `${other_cube.field}` join references. 7 dimensions, 6 metrics (revenue, food_revenue, drink_revenue, supply_cost, item_count, median_revenue). Relationships to orders and products.

### customers (LookML)

`models/lookml/customers.lkml` uses LookML syntax with `dimension`, `dimension_group`, `measure`, `sql_table_name`, and `${TABLE}` references. Auto-detected by `.lkml` extension. 5 metrics (customer_count, lifetime_spend, lifetime_spend_pretax, lifetime_tax_paid, total_lifetime_orders).

### locations (Malloy)

`models/malloy/locations.malloy` uses Malloy's `source: ... is duckdb.table(...) extend {}` syntax with `dimension:` and `measure:` declarations. 2 dimensions, 2 metrics (avg_tax_rate, location_count).

### products (OSI)

`models/osi/products.yml` uses the OSI (Open Semantic Interchange) format with `semantic_model:`, `datasets:`, and `fields:` keys. Expression dialects support multi-database targeting. Dimension-only model (product_name, product_type, product_description, is_food_item, is_drink_item, product_price).

## Yardstick SQL

Sidemantic has built-in support for Julian Hyde's [Measures in SQL](https://arxiv.org/abs/2307.15107) syntax. `SEMANTIC SELECT` / `AGGREGATE()` / `AT` modifiers enable context-aware aggregation directly against the model definitions, regardless of which format they were loaded from. Sidemantic's query rewriter translates these into standard SQL.

```bash
# Revenue by product with percent of total
sidemantic query "SEMANTIC SELECT
    order_items.product_name,
    AGGREGATE(order_items.revenue) AS revenue,
    100.0 * AGGREGATE(order_items.revenue) / AGGREGATE(order_items.revenue) AT (ALL) AS pct_of_total
FROM order_items
ORDER BY revenue DESC"

# See the generated SQL
sidemantic query --dry-run "SEMANTIC SELECT
    order_items.product_name,
    AGGREGATE(order_items.revenue) AS revenue,
    AGGREGATE(order_items.revenue) AT (ALL) AS total_revenue
FROM order_items"
```

`AGGREGATE()` wraps a measure and applies its defined aggregation (sum, count, avg, etc.) in the current grouping context. `AT (ALL)` overrides the grouping to compute across all rows, enabling percent-of-total calculations without window functions.

`yardstick_queries.sql` contains 9 example queries covering product revenue splits, food vs drink breakdowns, gross profit margins, order type analysis, customer segmentation, location performance, monthly revenue trends, new customer acquisition rates, and food/drink order mix over time.

## Quick start

```bash
# Clone with submodule
git clone --recursive <this-repo>
cd jaffle-shop-sidemantic

# Build the database (no dbt required)
uv run setup.py

# Run the demo
juv run demo.ipynb    # Jupyter notebook
# or
juv run demo.py       # percent-format script
```

`setup.py` reads the seed CSVs from the jaffle-shop submodule and builds `jaffle_shop.duckdb` with pure DuckDB SQL (no dbt needed). The demos auto-run it if the database doesn't exist.

## Project structure

```
.
├── jaffle-shop/                    # dbt project (git submodule)
├── models/
│   ├── metricflow/orders.yml       # MetricFlow: orders + graph metrics
│   ├── cube/order_items.yml        # Cube: order items
│   ├── lookml/customers.lkml       # LookML: customers
│   ├── malloy/locations.malloy     # Malloy: locations
│   └── osi/products.yml            # OSI: products (dimension-only)
├── setup.py                        # Build DuckDB from seed CSVs
├── sidemantic.yaml                 # Config (connection + model path)
├── yardstick_queries.sql           # SEMANTIC SELECT examples
├── demo.ipynb                      # Jupyter notebook demo
├── demo.py                         # Percent-format script demo
└── jaffle_shop.duckdb              # DuckDB database (generated)
```
