RETAIL RAW DATASET — UAE ONLINE RETAIL (SYNTHETIC TRAINING DATA)

All records are synthetic and created for interview practice. They do not represent real people or a real company. Currency: AED.

FILES
- orders_raw.csv: one row per order in the source system; contains an intentional duplicate export row and inconsistent status/date/payment formatting.
- order_items_raw.csv: one row per product line within an order; contains an intentional duplicate export row and inconsistent numeric formatting.
- customers_raw.csv: customer master export; contains an intentional duplicate row and inconsistent city/email formatting.
- products_raw.csv: product master export; contains an intentional duplicate row and inconsistent category/price formatting.
- returns_raw.csv: return events; contains an intentional duplicate export row, mixed dates/status text and refund formatting.

RELATIONSHIPS
- orders.customer_id -> customers.customer_id
- order_items.order_id -> orders.order_id
- order_items.product_id -> products.product_id
- returns.order_item_id -> order_items.order_item_id

BUSINESS NOTES
- Revenue at line level = quantity * unit_price * (1 - discount_pct / 100).
- For the practice tasks, count/revenue from Completed orders only unless a task says otherwise.
- For net revenue, subtract only approved refunds, and avoid subtracting the same return more than once. Partial returns are possible.
- Status values and some numeric/date fields are intentionally inconsistent. Inspect before cleaning.
- Do not delete every duplicate blindly: identify the business key and understand the effect on joins/aggregations.

TODAY'S PANDAS TASK (NO DASHBOARD DESIGN)
1. Load all five CSV files into separate DataFrames.
2. Inspect shape, columns, dtypes, missing values and exact duplicate rows for each table.
3. Standardize text fields (trim whitespace and normalize categorical casing).
4. Parse dates and numeric columns; handle currency prefixes, commas and percent signs.
5. Identify and handle duplicate export rows using appropriate business keys. Record how many rows were removed and why.
6. Create line_revenue = quantity * unit_price * (1 - discount_pct / 100).
7. Join order_items to orders and products; retain Completed orders for sales analysis.
8. Produce: monthly revenue + distinct order count; top 5 products by revenue; revenue by city.
9. Export an Excel workbook with sheets: Cleaned_Orders, Monthly_Sales, Top_Products, City_Sales.
10. Write three evidence-based business findings.

SCOPE LIMIT
For today's revision, finish steps 1-8 only if time is tight. Do not build a Power BI dashboard or automate scheduling.
