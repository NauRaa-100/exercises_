
from pathlib import Path
import pandas as pd
import numpy as np

# ==================================
# 1. PATHS
# ==================================

DATA_DIR = Path(r"E:\Rev-DataScience\RAW")

OUTPUT_DIR = DATA_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

# ==================================
# 2. LOAD DATA
# ==================================

dfs = {
    "customers": pd.read_csv(
        DATA_DIR / "customers_raw.csv",
        encoding="utf-8-sig"
    ),

    "orders": pd.read_csv(
        DATA_DIR / "orders_raw.csv",
        encoding="utf-8-sig"
    ),

    "order_items": pd.read_csv(
        DATA_DIR / "order_items_raw.csv",
        encoding="utf-8-sig"
    ),

    "products": pd.read_csv(
        DATA_DIR / "products_raw.csv",
        encoding="utf-8-sig"
    ),

    "returns": pd.read_csv(
        DATA_DIR / "returns_raw.csv",
        encoding="utf-8-sig"
    )
}

# ==================================
# 3. DATA INSPECTION
# ==================================

for name, data in dfs.items():

    print(f"\n========== {name.upper()} ==========")

    print("Shape:", data.shape)
    print("Missing:\n", data.isna().sum())
    print("Duplicates:", data.duplicated().sum())
    print("Columns:", data.columns.tolist())

# Standardize column names

for data in dfs.values():
    data.columns = (
        data.columns.str.strip().str.lower()
    )

# ==================================
# 4. REMOVE VERIFIED DUPLICATE KEYS
# ==================================

primary_keys = {
    "customers": "customer_id",
    "orders": "order_id",
    "order_items": "order_item_id",
    "products": "product_id",
    "returns": "return_id"
}

for name, key in primary_keys.items():

    data = dfs[name]

    duplicate_rows = data[
        data.duplicated(subset=key, keep=False)
    ]

    if not duplicate_rows.empty:

        conflicts = (
            duplicate_rows.groupby(key)
            .nunique(dropna=False)
            .gt(1)
            .any(axis=1)
        )

        if conflicts.any():
            raise ValueError(
                f"Conflicting duplicate keys in {name}"
            )

        dfs[name] = data.drop_duplicates(
            subset=key,
            keep="first"
        ).copy()

# ==================================
# 5. ACCESS DATAFRAMES
# ==================================

customers = dfs["customers"]
orders = dfs["orders"]
order_items = dfs["order_items"]
products = dfs["products"]
returns = dfs["returns"]

# ==================================
# 6. CLEAN TEXT
# ==================================

customers["city"] = (
    customers["city"].astype("string")
    .str.strip().str.title()
)

customers["email"] = (
    customers["email"].astype("string")
    .str.strip().str.lower()
)

orders["status"] = (
    orders["status"].astype("string")
    .str.strip().str.title()
)

orders["payment_method"] = (
    orders["payment_method"].astype("string")
    .str.strip().str.title()
)

products["category"] = (
    products["category"].astype("string")
    .str.strip().str.title()
)

returns["return_status"] = (
    returns["return_status"].astype("string")
    .str.strip().str.title()
)

# ==================================
# 7. CLEAN DATES
# ==================================

orders["order_date"] = pd.to_datetime(
    orders["order_date"],
    format="mixed",
    dayfirst=True,
    errors="coerce"
)

customers["signup_date"] = pd.to_datetime(
    customers["signup_date"],
    errors="coerce"
)

returns["return_date"] = pd.to_datetime(
    returns["return_date"],
    format="mixed",
    dayfirst=True,
    errors="coerce"
)

# ==================================
# 8. CLEAN NUMERIC COLUMNS
# ==================================

def clean_money(series):

    series = (
        series.astype("string")
        .str.replace(r"(?i)\bAED\b", "", regex=True)
        .str.replace(",", "", regex=False)
        .str.strip()
    )

    return pd.to_numeric(
        series,
        errors="coerce"
    )


order_items["unit_price"] = clean_money(
    order_items["unit_price"]
)

order_items["discount_pct"] = pd.to_numeric(
    order_items["discount_pct"]
    .astype("string")
    .str.replace("%", "", regex=False)
    .str.strip(),
    errors="coerce"
)

products["unit_cost"] = clean_money(
    products["unit_cost"]
)

products["list_price"] = clean_money(
    products["list_price"]
)

returns["refund_amount"] = clean_money(
    returns["refund_amount"]
)

# Business assumption for this exercise:
# Missing discount means no discount.
order_items["discount_pct"] = (
    order_items["discount_pct"].fillna(0)
)

# ==================================
# 9. DATA INTEGRATION
# ==================================

sales_lines = order_items.merge(
    orders[
        [
            "order_id",
            "customer_id",
            "employee_id",
            "order_date",
            "status",
            "payment_method"
        ]
    ],
    on="order_id",
    how="left",
    validate="many_to_one",
    indicator="order_match"
)

print(sales_lines["order_match"].value_counts())

sales_lines = sales_lines.drop(
    columns="order_match"
)

sales_lines = sales_lines.merge(
    products[
        [
            "product_id",
            "product_name",
            "category",
            "unit_cost"
        ]
    ],
    on="product_id",
    how="left",
    validate="many_to_one"
)

sales_lines = sales_lines.merge(
    customers[
        ["customer_id", "city"]
    ],
    on="customer_id",
    how="left",
    validate="many_to_one"
)

# ==================================
# 10. FEATURE ENGINEERING
# ==================================

sales_lines["gross_revenue"] = (
    sales_lines["quantity"] *
    sales_lines["unit_price"]
)

sales_lines["revenue_after_discount"] = (
    sales_lines["gross_revenue"] *
    (1 - sales_lines["discount_pct"] / 100)
).round(2)

# ==================================
# 11. APPROVED REFUNDS
# ==================================

approved_refunds = (
    returns.loc[
        returns["return_status"].eq("Approved")
    ]
    .groupby("order_item_id", as_index=False)
    .agg(
        approved_refund=("refund_amount", "sum")
    )
)

sales_lines = sales_lines.merge(
    approved_refunds,
    on="order_item_id",
    how="left",
    validate="one_to_one"
)

sales_lines["approved_refund"] = (
    sales_lines["approved_refund"].fillna(0)
)

sales_lines["net_revenue"] = (
    sales_lines["revenue_after_discount"] -
    sales_lines["approved_refund"]
).round(2)

# ==================================
# 12. COMPLETED SALES ONLY
# ==================================

completed_sales = sales_lines.loc[
    sales_lines["status"].eq("Completed")
].copy()

# ==================================
# 13. MONTHLY REVENUE
# ==================================

monthly_revenue = (
    completed_sales
    .dropna(subset=["order_date"])
    .assign(
        Month=lambda x:
            x["order_date"].dt.strftime("%Y-%m")
    )
    .groupby("Month", as_index=False)
    .agg(
        Monthly_Revenue=("net_revenue", "sum"),
        Revenue_After_Discount=(
            "revenue_after_discount", "sum"
        ),
        Num_of_Orders=("order_id", "nunique"),
        Quantity_Sold=("quantity", "sum")
    )
    .sort_values("Month")
)

# ==================================
# 14. TOP 10 PRODUCTS
# ==================================

top_products = (
    completed_sales
    .groupby(
        ["product_id", "product_name", "category"],
        as_index=False
    )
    .agg(
        Total_Revenue=("net_revenue", "sum")
    )
    .sort_values(
        "Total_Revenue",
        ascending=False
    )
    .head(10)
)

# ==================================
# 15. REVENUE BY CITY
# ==================================

city_revenue = (
    completed_sales
    .groupby("city", as_index=False, dropna=False)
    .agg(
        Total_Revenue=("net_revenue", "sum")
    )
    .sort_values(
        "Total_Revenue",
        ascending=False
    )
)

# ==================================
# 16. NUMBER OF ORDERS & AOV
# ==================================

order_summary = (
    completed_sales
    .groupby("order_id", as_index=False)
    .agg(
        Order_Value=(
            "revenue_after_discount", "sum"
        )
    )
)

num_of_orders = order_summary["order_id"].nunique()

aov = round(
    order_summary["Order_Value"].mean(),
    2
)

print("Completed Orders:", num_of_orders)
print("Average Order Value:", aov)

# ==================================
# 17. VALIDATION
# ==================================

print("Sales Lines:", len(sales_lines))
print("Completed Sales Lines:", len(completed_sales))

print(
    "Duplicate Order Items:",
    sales_lines["order_item_id"].duplicated().sum()
)

print(
    "Missing Unit Prices:",
    sales_lines["unit_price"].isna().sum()
)

# ==================================
# 18. EXPORT TO EXCEL
# ==================================

output_file = OUTPUT_DIR / "retail_analysis.xlsx"

with pd.ExcelWriter(
    output_file,
    engine="openpyxl",
    date_format="yyyy-mm-dd",
    datetime_format="yyyy-mm-dd"
) as writer:

    sales_lines.to_excel(
        writer,
        sheet_name="Cleaned_Orders",
        index=False
    )

    monthly_revenue.to_excel(
        writer,
        sheet_name="Monthly_Sales",
        index=False
    )

    top_products.to_excel(
        writer,
        sheet_name="Top_Products",
        index=False
    )

    city_revenue.to_excel(
        writer,
        sheet_name="City_Sales",
        index=False
    )

    # Improve the worksheet layout
    for worksheet in writer.book.worksheets:
        worksheet.freeze_panes = "A2"
        worksheet.auto_filter.ref = worksheet.dimensions

print("Report saved:", output_file)
