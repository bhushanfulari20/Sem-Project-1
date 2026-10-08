import pandas as pd
from pathlib import Path


# -------------------------------------------------
# SafeCart Database Folder
# -------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent


# -------------------------------------------------
# CSV File Paths
# -------------------------------------------------

PRODUCTS_FILE = BASE_DIR / "products.csv"
INVENTORY_FILE = BASE_DIR / "inventory.csv"
ORDERS_FILE = BASE_DIR / "orders.csv"
POLICIES_FILE = BASE_DIR / "policies.csv"
QUESTIONS_FILE = BASE_DIR / "customer_questions.csv"


# -------------------------------------------------
# Load CSV File
# -------------------------------------------------

def load_csv(file_path):
    try:
        return pd.read_csv(file_path)

    except FileNotFoundError:
        print(f"[ERROR] File not found: {file_path}")
        return pd.DataFrame()

    except Exception as e:
        print(f"[ERROR] Error loading {file_path}: {e}")
        return pd.DataFrame()


# -------------------------------------------------
# Load All Database Files
# -------------------------------------------------

def load_database():

    products = load_csv(PRODUCTS_FILE)
    inventory = load_csv(INVENTORY_FILE)
    orders = load_csv(ORDERS_FILE)
    policies = load_csv(POLICIES_FILE)
    questions = load_csv(QUESTIONS_FILE)

    return {
        "products": products,
        "inventory": inventory,
        "orders": orders,
        "policies": policies,
        "questions": questions
    }


# -------------------------------------------------
# Find Product
# -------------------------------------------------

def find_product(product_id):

    products = load_csv(PRODUCTS_FILE)

    if products.empty:
        return None

    result = products[
        products["product_id"].astype(str).str.upper()
        == str(product_id).upper()
    ]

    if result.empty:
        return None

    return result.iloc[0].to_dict()


# -------------------------------------------------
# Find Order
# -------------------------------------------------

def find_order(order_id):

    orders = load_csv(ORDERS_FILE)

    if orders.empty:
        return None

    result = orders[
        orders["order_id"].astype(str).str.upper()
        == str(order_id).upper()
    ]

    if result.empty:
        return None

    return result.iloc[0].to_dict()


# -------------------------------------------------
# Get Inventory
# -------------------------------------------------

def get_inventory(product_id):

    inventory = load_csv(INVENTORY_FILE)

    if inventory.empty:
        return None

    result = inventory[
        inventory["product_id"].astype(str).str.upper()
        == str(product_id).upper()
    ]

    if result.empty:
        return None

    return result.iloc[0].to_dict()


# -------------------------------------------------
# Get Policies
# -------------------------------------------------

def get_policies():

    policies = load_csv(POLICIES_FILE)

    if policies.empty:
        return []

    return policies.to_dict(orient="records")


# -------------------------------------------------
# Get Customer Questions
# -------------------------------------------------

def get_customer_questions():

    questions = load_csv(QUESTIONS_FILE)

    if questions.empty:
        return []

    return questions.to_dict(orient="records")


# -------------------------------------------------
# Test Database
# -------------------------------------------------

if __name__ == "__main__":

    database = load_database()

    print()
    print("=" * 50)
    print("       SafeCart Database Test")
    print("=" * 50)

    print(f"Products: {len(database['products'])}")
    print(f"Inventory Records: {len(database['inventory'])}")
    print(f"Orders: {len(database['orders'])}")
    print(f"Policies: {len(database['policies'])}")
    print(f"Customer Questions: {len(database['questions'])}")

    print("=" * 50)

    if (
        len(database["products"]) == 500
        and len(database["inventory"]) == 500
        and len(database["orders"]) == 500
        and len(database["policies"]) > 0
        and len(database["questions"]) == 500
    ):
        print("[PASS] DATABASE TEST PASSED!")
    else:
        print("[FAIL] DATABASE TEST FAILED!")
        print("Please check your CSV files.")

    print("=" * 50)