-- Yardstick SQL: measure-aware queries against sidemantic models
-- Sidemantic rewrites SEMANTIC SELECT / AGGREGATE() / AT into standard SQL
-- No DuckDB extension needed: measures come from the model definitions
-- Models loaded from 5 formats: MetricFlow, Cube, LookML, Malloy, OSI

-- 1. Revenue by product with percent of total
SEMANTIC SELECT
    order_items.product_name,
    AGGREGATE(order_items.revenue) AS revenue,
    100.0 * AGGREGATE(order_items.revenue) / AGGREGATE(order_items.revenue) AT (ALL) AS pct_of_total,
    AGGREGATE(order_items.item_count) AS units_sold
FROM order_items
ORDER BY revenue DESC;

-- 2. Food vs drink breakdown
SEMANTIC SELECT
    order_items.product_name,
    AGGREGATE(order_items.food_revenue) AS food_rev,
    AGGREGATE(order_items.drink_revenue) AS drink_rev,
    AGGREGATE(order_items.revenue) AS total_rev,
    100.0 * AGGREGATE(order_items.food_revenue) / AGGREGATE(order_items.revenue) AS food_pct
FROM order_items
ORDER BY total_rev DESC;

-- 3. Gross profit analysis by product
SEMANTIC SELECT
    order_items.product_name,
    AGGREGATE(order_items.revenue) AS revenue,
    AGGREGATE(order_items.supply_cost) AS cost,
    AGGREGATE(order_items.revenue) - AGGREGATE(order_items.supply_cost) AS gross_profit,
    100.0 * (AGGREGATE(order_items.revenue) - AGGREGATE(order_items.supply_cost)) / AGGREGATE(order_items.revenue) AS margin_pct
FROM order_items
ORDER BY gross_profit DESC;

-- 4. Order totals with percent of total (AT modifier)
SEMANTIC SELECT
    orders.is_food_order,
    AGGREGATE(orders.order_count) AS orders,
    AGGREGATE(orders.order_total) AS revenue,
    100.0 * AGGREGATE(orders.order_total) / AGGREGATE(orders.order_total) AT (ALL) AS pct_of_revenue
FROM orders
ORDER BY revenue DESC;

-- 5. Customer lifetime value with percent of total
SEMANTIC SELECT
    customers.customer_type,
    AGGREGATE(customers.customer_count) AS customers,
    AGGREGATE(customers.lifetime_spend) AS total_spend,
    AGGREGATE(customers.total_lifetime_orders) AS total_orders,
    100.0 * AGGREGATE(customers.customer_count) / AGGREGATE(customers.customer_count) AT (ALL) AS pct_of_customers
FROM customers;

-- 6. Location performance
SEMANTIC SELECT
    locations.location_name,
    AGGREGATE(locations.avg_tax_rate) AS tax_rate,
    AGGREGATE(locations.location_count) AS count
FROM locations
ORDER BY tax_rate DESC;

-- 7. Monthly revenue with percent of annual total (time comparison)
SEMANTIC SELECT
    orders.ordered_at,
    AGGREGATE(orders.order_total) AS monthly_revenue,
    AGGREGATE(orders.order_count) AS monthly_orders,
    100.0 * AGGREGATE(orders.order_total) / AGGREGATE(orders.order_total) AT (ALL) AS pct_of_annual
FROM orders
ORDER BY orders.ordered_at;

-- 8. New customer acquisition rate by month
SEMANTIC SELECT
    orders.ordered_at,
    AGGREGATE(orders.order_count) AS total_orders,
    AGGREGATE(orders.new_customer_order_count) AS new_customer_orders,
    100.0 * AGGREGATE(orders.new_customer_order_count) / AGGREGATE(orders.order_count) AS new_customer_pct
FROM orders
ORDER BY orders.ordered_at;

-- 9. Food vs drink order mix over time
SEMANTIC SELECT
    orders.ordered_at,
    AGGREGATE(orders.order_count) AS total_orders,
    AGGREGATE(orders.food_order_count) AS food_orders,
    AGGREGATE(orders.drink_order_count) AS drink_orders,
    100.0 * AGGREGATE(orders.food_order_count) / AGGREGATE(orders.order_count) AS food_pct,
    100.0 * AGGREGATE(orders.drink_order_count) / AGGREGATE(orders.order_count) AS drink_pct
FROM orders
ORDER BY orders.ordered_at;
