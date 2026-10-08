import pandas as pd
from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parent

PRODUCTS_FILE = BASE_DIR / "products.csv"
INVENTORY_FILE = BASE_DIR / "inventory.csv"
ORDERS_FILE = BASE_DIR / "orders.csv"
POLICIES_FILE = BASE_DIR / "policies.csv"
QUESTIONS_FILE = BASE_DIR / "customer_questions.csv"

def run_db_validation():
    errors = []
    print("=" * 60)
    print("       SafeCart Comprehensive Database Consistency Test")
    print("=" * 60)

    # 1. Existence and Load
    for name, path in [
        ("Products", PRODUCTS_FILE),
        ("Inventory", INVENTORY_FILE),
        ("Orders", ORDERS_FILE),
        ("Policies", POLICIES_FILE),
        ("Questions", QUESTIONS_FILE),
    ]:
        if not path.exists():
            errors.append(f"Missing file: {name} ({path})")

    if errors:
        for err in errors:
            print(f"[FAIL] {err}")
        return False

    products = pd.read_csv(PRODUCTS_FILE)
    inventory = pd.read_csv(INVENTORY_FILE)
    orders = pd.read_csv(ORDERS_FILE)
    policies = pd.read_csv(POLICIES_FILE)
    questions = pd.read_csv(QUESTIONS_FILE)

    print(f"Products count: {len(products)}")
    print(f"Inventory count: {len(inventory)}")
    print(f"Orders count: {len(orders)}")
    print(f"Questions count: {len(questions)}")
    print(f"Policies count: {len(policies)}")

    # 2. Record counts
    if len(products) != 500:
        errors.append(f"Products count is {len(products)}, expected 500")
    if len(inventory) != 500:
        errors.append(f"Inventory count is {len(inventory)}, expected 500")
    if len(orders) != 500:
        errors.append(f"Orders count is {len(orders)}, expected 500")
    if len(questions) != 500:
        errors.append(f"Questions count is {len(questions)}, expected 500")
    if len(policies) == 0:
        errors.append("Policies table is empty")

    # 3. Duplicate checks
    if products["product_id"].duplicated().any():
        dups = products[products["product_id"].duplicated()]["product_id"].tolist()
        errors.append(f"Duplicate product_id in products.csv: {dups}")

    if inventory["product_id"].duplicated().any():
        dups = inventory[inventory["product_id"].duplicated()]["product_id"].tolist()
        errors.append(f"Duplicate product_id in inventory.csv: {dups}")

    if orders["order_id"].duplicated().any():
        dups = orders[orders["order_id"].duplicated()]["order_id"].tolist()
        errors.append(f"Duplicate order_id in orders.csv: {dups}")

    if questions["question_id"].duplicated().any():
        dups = questions[questions["question_id"].duplicated()]["question_id"].tolist()
        errors.append(f"Duplicate question_id in customer_questions.csv: {dups}")

    # 4. Foreign key checks
    prod_ids = set(products["product_id"].astype(str).str.upper())
    inv_prod_ids = set(inventory["product_id"].astype(str).str.upper())
    ord_prod_ids = set(orders["product_id"].astype(str).str.upper())

    invalid_inv_ids = inv_prod_ids - prod_ids
    if invalid_inv_ids:
        errors.append(f"Inventory has product_ids not in products.csv: {invalid_inv_ids}")

    invalid_ord_ids = ord_prod_ids - prod_ids
    if invalid_ord_ids:
        errors.append(f"Orders has product_ids not in products.csv: {invalid_ord_ids}")

    # 5. Required columns and nulls
    for col in ["product_id", "product_name", "price"]:
        if col not in products.columns or products[col].isnull().any():
            errors.append(f"Column products.{col} missing or contains nulls")

    for col in ["product_id", "quantity"]:
        if col not in inventory.columns or inventory[col].isnull().any():
            errors.append(f"Column inventory.{col} missing or contains nulls")

    for col in ["order_id", "product_id", "refundable"]:
        if col not in orders.columns or orders[col].isnull().any():
            errors.append(f"Column orders.{col} missing or contains nulls")

    # 6. Numeric checks
    if not pd.to_numeric(products["price"], errors="coerce").notnull().all():
        errors.append("Non-numeric price values in products.csv")

    if not pd.to_numeric(inventory["quantity"], errors="coerce").notnull().all():
        errors.append("Non-numeric quantity values in inventory.csv")

    print("-" * 60)
    if errors:
        for err in errors:
            print(f"[FAIL] {err}")
        print("[FAIL] Comprehensive Database Test FAILED!")
        print("=" * 60)
        return False
    else:
        print("[PASS] All relationships, IDs, types, and counts verified!")
        print("[PASS] Comprehensive Database Test PASSED!")
        print("=" * 60)
        return True

if __name__ == "__main__":
    success = run_db_validation()
    sys.exit(0 if success else 1)
