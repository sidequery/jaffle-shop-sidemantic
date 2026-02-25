view: customers {
  sql_table_name: main.customers ;;

  dimension: customer_id {
    primary_key: yes
    type: string
    sql: ${TABLE}.customer_id ;;
  }

  dimension: customer_name {
    type: string
    sql: ${TABLE}.customer_name ;;
  }

  dimension: customer_type {
    type: string
    sql: ${TABLE}.customer_type ;;
  }

  dimension_group: first_ordered {
    type: time
    timeframes: [raw, date, week, month, quarter, year]
    sql: ${TABLE}.first_ordered_at ;;
    datatype: date
  }

  dimension_group: last_ordered {
    type: time
    timeframes: [raw, date, week, month, quarter, year]
    sql: ${TABLE}.last_ordered_at ;;
    datatype: date
  }

  measure: customer_count {
    type: count_distinct
    sql: ${TABLE}.customer_id ;;
  }

  measure: lifetime_spend {
    type: sum
    sql: ${TABLE}.lifetime_spend ;;
    value_format_name: usd
  }

  measure: lifetime_spend_pretax {
    type: sum
    sql: ${TABLE}.lifetime_spend_pretax ;;
    value_format_name: usd
  }

  measure: lifetime_tax_paid {
    type: sum
    sql: ${TABLE}.lifetime_tax_paid ;;
    value_format_name: usd
  }

  measure: total_lifetime_orders {
    type: sum
    sql: ${TABLE}.count_lifetime_orders ;;
  }
}
