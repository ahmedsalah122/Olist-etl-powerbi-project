import pandas as pd
import os
import logging
from pathlib import Path

# ── setup ──────────────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(message)s")
log = logging.getLogger(__name__)

RAW_DIR    = "raw"          # put the 8 Kaggle CSVs here
OUT_DIR    = "output/star_schema"
ENCODING   = "utf-8-sig"   # Power BI loves this


# ══════════════════════════════════════════════════════════════════════════════
# 1. EXTRACT
# ══════════════════════════════════════════════════════════════════════════════
def extract(raw_dir: str) -> dict[str, pd.DataFrame]:
    """Read every CSV we need from the raw folder."""
    log.info("── EXTRACT ──────────────────────────────────────")

    files = {
        "orders":        "olist_orders_dataset.csv",
        "order_items":   "olist_order_items_dataset.csv",
        "order_pays":    "olist_order_payments_dataset.csv",
        "order_reviews": "olist_order_reviews_dataset.csv",
        "customers":     "olist_customers_dataset.csv",
        "products":      "olist_products_dataset.csv",
        "sellers":       "olist_sellers_dataset.csv",
        "category_xlat": "product_category_name_translation.csv",
        "geo":           "olist_geolocation_dataset.csv",
    }

    raw = {}
    for key, fname in files.items():
        path = os.path.join(raw_dir, fname)
        raw[key] = pd.read_csv(path, low_memory=False)
        log.info(f"  {key:15s} → {len(raw[key]):,} rows, {raw[key].shape[1]} cols")

    return raw


# ══════════════════════════════════════════════════════════════════════════════
# 2. CLEAN
# ══════════════════════════════════════════════════════════════════════════════
def _clean_str(series: pd.Series) -> pd.Series:
    """Strip whitespace and title-case a text column."""
    return series.fillna("unknown").str.strip().str.title()


def _to_date(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    """Parse timestamp columns to datetime."""
    for c in cols:
        if c in df.columns:
            df[c] = pd.to_datetime(df[c], errors="coerce")
    return df


def clean(raw: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    """Fix data types, fill nulls, remove dupes."""
    log.info("── CLEAN ────────────────────────────────────────")

    # orders
    o = raw["orders"].copy()
    o = _to_date(o, ["order_purchase_timestamp", "order_approved_at",
                     "order_delivered_carrier_date",
                     "order_delivered_customer_date",
                     "order_estimated_delivery_date"])
    o["order_status"] = _clean_str(o["order_status"])
    o.drop_duplicates("order_id", inplace=True)

    # order items
    oi = raw["order_items"].copy()
    oi["price"]         = pd.to_numeric(oi["price"],         errors="coerce").fillna(0)
    oi["freight_value"] = pd.to_numeric(oi["freight_value"], errors="coerce").fillna(0)
    oi = oi[oi["price"] >= 0]                  # drop negative prices
    oi.drop_duplicates(inplace=True)

    # payments
    pay = raw["order_pays"].copy()
    pay["payment_value"] = pd.to_numeric(pay["payment_value"], errors="coerce").fillna(0)
    pay["payment_installments"] = pd.to_numeric(pay["payment_installments"], errors="coerce").fillna(1)
    pay["payment_type"] = _clean_str(pay["payment_type"])
    pay.drop_duplicates(inplace=True)

    # reviews
    rev = raw["order_reviews"].copy()
    rev["review_score"] = pd.to_numeric(rev["review_score"], errors="coerce")
    rev = rev[(rev["review_score"] >= 1) & (rev["review_score"] <= 5)]
    rev = _to_date(rev, ["review_creation_date", "review_answer_timestamp"])
    rev.drop_duplicates("review_id", inplace=True)

    # customers
    cust = raw["customers"].copy()
    cust["customer_city"]  = _clean_str(cust["customer_city"])
    cust["customer_state"] = cust["customer_state"].fillna("XX").str.upper().str.strip()
    cust.drop_duplicates("customer_id", inplace=True)

    # products
    prod = raw["products"].copy()
    cat  = raw["category_xlat"].copy()
    prod = prod.merge(cat, on="product_category_name", how="left")
    prod["product_category_name_english"] = _clean_str(
        prod.get("product_category_name_english", prod["product_category_name"])
    )
    num_cols = ["product_weight_g", "product_length_cm",
                "product_height_cm", "product_width_cm",
                "product_photos_qty", "product_name_lenght",
                "product_description_lenght"]
    for c in num_cols:
        if c in prod.columns:
            prod[c] = pd.to_numeric(prod[c], errors="coerce").fillna(0)
    prod.drop_duplicates("product_id", inplace=True)

    # sellers
    sel = raw["sellers"].copy()
    sel["seller_city"]  = _clean_str(sel["seller_city"])
    sel["seller_state"] = sel["seller_state"].fillna("XX").str.upper().str.strip()
    sel.drop_duplicates("seller_id", inplace=True)

    log.info("  cleaning done ✓")
    return dict(orders=o, order_items=oi, payments=pay,
                reviews=rev, customers=cust, products=prod, sellers=sel)


# ══════════════════════════════════════════════════════════════════════════════
# 3. TRANSFORM  →  Star Schema
# ══════════════════════════════════════════════════════════════════════════════

# helper: add a surrogate key
def _add_sk(df: pd.DataFrame, sk_name: str) -> pd.DataFrame:
    df = df.reset_index(drop=True)
    df.insert(0, sk_name, range(1, len(df) + 1))
    return df


def build_dim_customer(customers: pd.DataFrame) -> pd.DataFrame:
    log.info("  building dim_customer …")
    dim = customers[["customer_id", "customer_unique_id",
                     "customer_city", "customer_state",
                     "customer_zip_code_prefix"]].copy()
    dim.rename(columns={"customer_zip_code_prefix": "customer_zip"}, inplace=True)
    return _add_sk(dim, "customer_sk")


def build_dim_product(products: pd.DataFrame) -> pd.DataFrame:
    log.info("  building dim_product …")
    dim = products[["product_id",
                    "product_category_name_english",
                    "product_weight_g", "product_length_cm",
                    "product_height_cm", "product_width_cm",
                    "product_photos_qty"]].copy()
    dim.rename(columns={"product_category_name_english": "category"}, inplace=True)
    return _add_sk(dim, "product_sk")


def build_dim_seller(sellers: pd.DataFrame) -> pd.DataFrame:
    log.info("  building dim_seller …")
    dim = sellers[["seller_id", "seller_city",
                   "seller_state", "seller_zip_code_prefix"]].copy()
    dim.rename(columns={"seller_zip_code_prefix": "seller_zip"}, inplace=True)
    return _add_sk(dim, "seller_sk")


def build_dim_payment(payments: pd.DataFrame) -> pd.DataFrame:
    """One row per order (take the dominant / max-value payment type)."""
    log.info("  building dim_payment …")
    # pick the payment with the highest value per order
    idx = payments.groupby("order_id")["payment_value"].idxmax()
    dim = payments.loc[idx, ["order_id", "payment_type",
                             "payment_installments"]].copy()
    return _add_sk(dim, "payment_sk")


def build_dim_review(reviews: pd.DataFrame) -> pd.DataFrame:
    """One row per order (keep the latest review)."""
    log.info("  building dim_review …")
    latest = (reviews.sort_values("review_answer_timestamp")
                     .drop_duplicates("order_id", keep="last"))
    dim = latest[["order_id", "review_score",
                  "review_creation_date"]].copy()
    dim["review_creation_date"] = dim["review_creation_date"].dt.date
    return _add_sk(dim, "review_sk")


def build_fact_orders(
    orders:     pd.DataFrame,
    order_items: pd.DataFrame,
    dim_customer: pd.DataFrame,
    dim_product:  pd.DataFrame,
    dim_seller:   pd.DataFrame,
    dim_payment:  pd.DataFrame,
    dim_review:   pd.DataFrame,
) -> pd.DataFrame:
    log.info("  building fact_order_items …")

    # aggregate payments per order
    pay_agg = (order_items.groupby("order_id")
                          .agg(total_items=("order_item_id", "count"),
                               total_price=("price", "sum"),
                               total_freight=("freight_value", "sum"))
                          .reset_index())

    # base: orders + aggregated items
    fact = orders.merge(pay_agg, on="order_id", how="inner")

    # bring in one row per order_item so we keep product + seller granularity
    fact = fact.merge(order_items[["order_id", "order_item_id",
                                   "product_id", "seller_id",
                                   "price", "freight_value"]],
                      on="order_id", how="left")

    # date columns we want to keep
    fact["purchase_date"]           = fact["order_purchase_timestamp"].dt.date
    fact["estimated_delivery_date"] = fact["order_estimated_delivery_date"].dt.date
    fact["actual_delivery_date"]    = fact["order_delivered_customer_date"].dt.date

    # delivery days
    fact["delivery_days"] = (
        fact["order_delivered_customer_date"] - fact["order_purchase_timestamp"]
    ).dt.days

    # early/late flag
    fact["delivered_on_time"] = (
        fact["order_delivered_customer_date"] <= fact["order_estimated_delivery_date"]
    ).astype("Int8")

    # ── join surrogate keys ──────────────────────────────────────────────────
    # customer
    fact = fact.merge(dim_customer[["customer_id", "customer_sk"]],
                      on="customer_id", how="left")

    # product
    fact = fact.merge(dim_product[["product_id", "product_sk"]],
                      on="product_id", how="left")

    # seller
    fact = fact.merge(dim_seller[["seller_id", "seller_sk"]],
                      on="seller_id", how="left")

    # payment
    fact = fact.merge(dim_payment[["order_id", "payment_sk"]],
                      on="order_id", how="left")

    # review
    fact = fact.merge(dim_review[["order_id", "review_sk"]],
                      on="order_id", how="left")

    # ── keep only the columns the fact table needs ───────────────────────────
    keep = [
        "order_id", "order_item_id", "order_status",
        "purchase_date", "estimated_delivery_date", "actual_delivery_date",
        # measures
        "price", "freight_value", "total_price", "total_freight",
        "total_items", "delivery_days", "delivered_on_time",
        # foreign keys
        "customer_sk", "product_sk", "seller_sk",
        "payment_sk", "review_sk",
    ]
    fact = fact[[c for c in keep if c in fact.columns]].copy()
    fact.fillna({"delivery_days": -1, "delivered_on_time": -1}, inplace=True)

    log.info(f"  fact rows: {len(fact):,}")
    return fact


def transform(clean_data: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    log.info("── TRANSFORM ────────────────────────────────────")

    dim_customer = build_dim_customer(clean_data["customers"])
    dim_product  = build_dim_product(clean_data["products"])
    dim_seller   = build_dim_seller(clean_data["sellers"])
    dim_payment  = build_dim_payment(clean_data["payments"])
    dim_review   = build_dim_review(clean_data["reviews"])

    fact = build_fact_orders(
        clean_data["orders"],
        clean_data["order_items"],
        dim_customer, dim_product, dim_seller,
        dim_payment, dim_review,
    )

    return {
        "dim_customer": dim_customer,
        "dim_product":  dim_product,
        "dim_seller":   dim_seller,
        "dim_payment":  dim_payment,
        "dim_review":   dim_review,
        "fact_order_items": fact,
    }


# ══════════════════════════════════════════════════════════════════════════════
# 4. LOAD
# ══════════════════════════════════════════════════════════════════════════════
def load(tables: dict[str, pd.DataFrame], out_dir: str) -> None:
    log.info("── LOAD ─────────────────────────────────────────")
    Path(out_dir).mkdir(parents=True, exist_ok=True)

    for name, df in tables.items():
        path = os.path.join(out_dir, f"{name}.csv")
        df.to_csv(path, index=False, encoding=ENCODING)
        log.info(f"  saved {name}.csv  ({len(df):,} rows)")

    log.info("── DONE ✓ ───────────────────────────────────────")


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    raw_data   = extract(RAW_DIR)
    clean_data = clean(raw_data)
    star       = transform(clean_data)
    load(star, OUT_DIR)
