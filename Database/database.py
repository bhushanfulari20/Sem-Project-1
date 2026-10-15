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
USERS_FILE = BASE_DIR / "users.csv"


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
    users = load_csv(USERS_FILE)

    return {
        "products": products,
        "inventory": inventory,
        "orders": orders,
        "policies": policies,
        "questions": questions,
        "users": users
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
# Search Products
# -------------------------------------------------

def search_products(query="", category=None, limit=None, offset=0):
    products = load_csv(PRODUCTS_FILE)
    if products.empty:
        return []

    inventory = load_csv(INVENTORY_FILE)
    inv_map = {}
    if not inventory.empty:
        for _, row in inventory.iterrows():
            inv_map[str(row["product_id"]).upper()] = int(row["quantity"])

    filtered = products
    if category and str(category).strip().lower() != "all":
        filtered = filtered[
            filtered["category"].astype(str).str.lower()
            == str(category).strip().lower()
        ]

    if query and str(query).strip():
        q = str(query).strip().lower()
        mask = (
            filtered["product_id"].astype(str).str.lower().str.contains(q, regex=False)
            | filtered["product_name"].astype(str).str.lower().str.contains(q, regex=False)
            | filtered["category"].astype(str).str.lower().str.contains(q, regex=False)
            | filtered["description"].astype(str).str.lower().str.contains(q, regex=False)
        )
        filtered = filtered[mask]

    if offset > 0:
        filtered = filtered.iloc[offset:]
    if limit is not None:
        filtered = filtered.head(limit)

    results = []
    for _, row in filtered.iterrows():
        item = row.to_dict()
        pid = str(item["product_id"]).upper()
        qty = inv_map.get(pid, 0)
        item["quantity"] = qty
        item["in_stock"] = qty > 0
        results.append(item)

    return results


def count_products(query="", category=None):
    products = load_csv(PRODUCTS_FILE)
    if products.empty:
        return 0

    filtered = products
    if category and str(category).strip().lower() != "all":
        filtered = filtered[
            filtered["category"].astype(str).str.lower()
            == str(category).strip().lower()
        ]

    if query and str(query).strip():
        q = str(query).strip().lower()
        mask = (
            filtered["product_id"].astype(str).str.lower().str.contains(q, regex=False)
            | filtered["product_name"].astype(str).str.lower().str.contains(q, regex=False)
            | filtered["category"].astype(str).str.lower().str.contains(q, regex=False)
            | filtered["description"].astype(str).str.lower().str.contains(q, regex=False)
        )
        filtered = filtered[mask]

    return len(filtered)


def get_categories():
    products = load_csv(PRODUCTS_FILE)
    if products.empty or "category" not in products.columns:
        return []
    cats = sorted(products["category"].dropna().unique().tolist())
    return cats


# -------------------------------------------------
# Get Product with Live Inventory
# -------------------------------------------------

def get_product_with_inventory(product_id):
    product = find_product(product_id)
    if not product:
        return None
    inv = get_inventory(product_id)
    qty = int(inv.get("quantity", 0)) if inv else 0
    product["quantity"] = qty
    product["in_stock"] = qty > 0
    return product


# -------------------------------------------------
# Update Inventory
# -------------------------------------------------

def update_inventory(product_id, quantity_diff):
    inventory = load_csv(INVENTORY_FILE)
    if inventory.empty:
        return None

    pid_str = str(product_id).strip().upper()
    mask = inventory["product_id"].astype(str).str.upper() == pid_str
    if not mask.any():
        return None

    idx = inventory[mask].index[0]
    current_qty = int(inventory.at[idx, "quantity"])
    new_qty = max(0, current_qty + quantity_diff)
    inventory.at[idx, "quantity"] = new_qty
    inventory.to_csv(INVENTORY_FILE, index=False)
    return {"product_id": pid_str, "quantity": new_qty}


def set_inventory(product_id, quantity):
    """Set absolute inventory stock quantity for a product in SafeCart database."""
    inventory = load_csv(INVENTORY_FILE)
    pid_str = str(product_id).strip().upper()
    qty = max(0, int(quantity))

    if not inventory.empty:
        mask = inventory["product_id"].astype(str).str.upper() == pid_str
        if mask.any():
            idx = inventory[mask].index[0]
            inventory.at[idx, "quantity"] = qty
            inventory.to_csv(INVENTORY_FILE, index=False)
            return {"product_id": pid_str, "quantity": qty}

    # If not present in inventory.csv, add new record
    new_row = {"product_id": pid_str, "quantity": qty}
    new_df = pd.DataFrame([new_row])
    inventory = pd.concat([inventory, new_df], ignore_index=True) if not inventory.empty else new_df
    inventory.to_csv(INVENTORY_FILE, index=False)
    return {"product_id": pid_str, "quantity": qty}


# -------------------------------------------------
# Product CRUD & Database Synchronization
# -------------------------------------------------

def add_product(product_name, category, price, description="", initial_stock=10, product_id=None, image_url=None):
    """Add a new product to SafeCart database and synchronize inventory."""
    products = load_csv(PRODUCTS_FILE)
    
    if not product_name or not category:
        raise ValueError("Product name and category are required.")

    try:
        numeric_price = int(float(price))
    except (ValueError, TypeError):
        raise ValueError("Price must be a valid number.")

    if not product_id:
        # Generate next available product ID (e.g. P501)
        numeric_ids = []
        if not products.empty and "product_id" in products.columns:
            for pid in products["product_id"].astype(str):
                digits = "".join(filter(str.isdigit, pid))
                if digits:
                    numeric_ids.append(int(digits))
        next_num = (max(numeric_ids) + 1) if numeric_ids else 1
        new_pid = f"P{next_num:03d}"
    else:
        new_pid = str(product_id).strip().upper()
        if not products.empty and (products["product_id"].astype(str).str.upper() == new_pid).any():
            raise ValueError(f"Product ID '{new_pid}' already exists in database.")

    final_image_url = (str(image_url).strip() if image_url and str(image_url).strip()
                       else f"https://images.unsplash.com/photo-1526170375885-4d8ecf77b99f?w=500&auto=format&fit=crop&q=80&sig={new_pid}")

    new_prod_row = {
        "product_id": new_pid,
        "product_name": str(product_name).strip(),
        "category": str(category).strip(),
        "price": numeric_price,
        "description": str(description).strip(),
        "image_url": final_image_url
    }

    new_df = pd.DataFrame([new_prod_row])
    products = pd.concat([products, new_df], ignore_index=True) if not products.empty else new_df
    products.to_csv(PRODUCTS_FILE, index=False)

    # Synchronize inventory
    set_inventory(new_pid, initial_stock)

    return {
        **new_prod_row,
        "quantity": max(0, int(initial_stock)),
        "in_stock": int(initial_stock) > 0
    }


def update_product(product_id, product_name=None, category=None, price=None, description=None, quantity=None, image_url=None):
    """Update existing product details and stock in SafeCart database."""
    products = load_csv(PRODUCTS_FILE)
    if products.empty:
        raise ValueError("Products database is empty.")

    pid_str = str(product_id).strip().upper()
    mask = products["product_id"].astype(str).str.upper() == pid_str
    if not mask.any():
        raise ValueError(f"Product '{pid_str}' not found in database.")

    idx = products[mask].index[0]

    if product_name is not None and str(product_name).strip():
        products.at[idx, "product_name"] = str(product_name).strip()
    if category is not None and str(category).strip():
        products.at[idx, "category"] = str(category).strip()
    if price is not None:
        try:
            products.at[idx, "price"] = int(float(price))
        except (ValueError, TypeError):
            raise ValueError("Price must be a valid number.")
    if description is not None:
        products.at[idx, "description"] = str(description).strip()
    if image_url is not None and str(image_url).strip():
        products.at[idx, "image_url"] = str(image_url).strip()

    products.to_csv(PRODUCTS_FILE, index=False)

    # If quantity change requested, update inventory as well
    if quantity is not None:
        set_inventory(pid_str, quantity)

    return get_product_with_inventory(pid_str)


def delete_product(product_id):
    """Delete product and corresponding inventory record from SafeCart database."""
    products = load_csv(PRODUCTS_FILE)
    inventory = load_csv(INVENTORY_FILE)

    pid_str = str(product_id).strip().upper()

    if not products.empty:
        products = products[products["product_id"].astype(str).str.upper() != pid_str]
        products.to_csv(PRODUCTS_FILE, index=False)

    if not inventory.empty:
        inventory = inventory[inventory["product_id"].astype(str).str.upper() != pid_str]
        inventory.to_csv(INVENTORY_FILE, index=False)

    return True


# -------------------------------------------------
# Create Order
# -------------------------------------------------

def create_order(product_id, customer_name=None, order_date=None, delivery_date=None, quantity=1,
                 customer_email=None, shipping_address=None, payment_method=None):
    from datetime import datetime, timedelta

    product = find_product(product_id)
    if not product:
        raise ValueError(f"Product {product_id} not found in database.")

    inv = get_inventory(product_id)
    qty = int(inv.get("quantity", 0)) if inv else 0
    if qty <= 0:
        raise ValueError(f"Product {product['product_name']} ({product_id}) is out of stock.")
    if qty < quantity:
        raise ValueError(f"Insufficient stock for {product['product_name']} ({product_id}). Available: {qty}, requested: {quantity}.")

    # Deduct quantity units from inventory
    update_inventory(product_id, -quantity)

    orders = load_csv(ORDERS_FILE)
    # Generate next order ID
    next_num = 1
    if not orders.empty and "order_id" in orders.columns:
        numeric_ids = []
        for oid in orders["order_id"].astype(str):
            if oid.startswith("O") and oid[1:].isdigit():
                numeric_ids.append(int(oid[1:]))
        if numeric_ids:
            next_num = max(numeric_ids) + 1

    new_order_id = f"O{next_num:03d}"
    now = datetime.now()
    if not order_date:
        order_date = now.strftime("%Y-%m-%d")
    if not delivery_date:
        delivery_date = (now + timedelta(days=4)).strftime("%Y-%m-%d")

    c_name = str(customer_name or "Amazon Customer").strip()
    c_email = str(customer_email or "customer@amazon.in").strip()
    s_addr = str(shipping_address or "202 Marine Drive, Mumbai, India").strip()
    p_method = str(payment_method or "Simulated Demo Payment").strip()

    new_row = {
        "order_id": new_order_id,
        "product_id": str(product["product_id"]).upper(),
        "order_date": order_date,
        "delivery_date": delivery_date,
        "refundable": "Yes",
        "refunded": "No",
        "customer_name": c_name,
        "customer_email": c_email,
        "shipping_address": s_addr,
        "payment_method": p_method
    }

    new_df = pd.DataFrame([new_row])
    orders = pd.concat([orders, new_df], ignore_index=True)
    orders.to_csv(ORDERS_FILE, index=False)

    new_row["product_name"] = product.get("product_name")
    new_row["price"] = product.get("price")
    new_row["quantity"] = quantity
    return new_row


# -------------------------------------------------
# Get All Orders
# -------------------------------------------------

def get_all_orders(limit=None):
    orders = load_csv(ORDERS_FILE)
    if orders.empty:
        return []
    products = load_csv(PRODUCTS_FILE)
    prod_map = {}
    if not products.empty:
        for _, row in products.iterrows():
            prod_map[str(row["product_id"]).upper()] = row.to_dict()

    results = []
    df = orders.tail(limit) if limit else orders
    for _, row in df.iterrows():
        item = row.to_dict()
        pid = str(item.get("product_id", "")).upper()
        prod = prod_map.get(pid, {})
        item["product_name"] = prod.get("product_name", "Product")
        item["price"] = prod.get("price", "N/A")
        results.append(item)
    return results


# -------------------------------------------------
# User Management
# -------------------------------------------------

def load_users():
    return load_csv(USERS_FILE)


def find_user(email_or_id):
    users = load_csv(USERS_FILE)
    if users.empty:
        return None
    val = str(email_or_id).strip().lower()
    result = users[
        (users["email"].astype(str).str.lower() == val)
        | (users["user_id"].astype(str).str.lower() == val)
    ]
    if result.empty:
        return None
    return result.iloc[0].to_dict()


def authenticate_user(email, password):
    user = find_user(email)
    if not user:
        return None
    if str(user.get("password", "")).strip() == str(password).strip():
        safe_user = dict(user)
        safe_user.pop("password", None)
        return safe_user
    return None


def create_user(name, email, password, address="India"):
    users = load_csv(USERS_FILE)
    if not users.empty and (users["email"].astype(str).str.lower() == str(email).strip().lower()).any():
        raise ValueError("User with this email already exists.")

    next_num = len(users) + 1 if not users.empty else 1
    new_user_id = f"U{next_num:03d}"
    new_row = {
        "user_id": new_user_id,
        "name": name.strip(),
        "email": email.strip(),
        "password": password.strip(),
        "address": address.strip()
    }
    new_df = pd.DataFrame([new_row])
    users = pd.concat([users, new_df], ignore_index=True) if not users.empty else new_df
    users.to_csv(USERS_FILE, index=False)
    safe_user = dict(new_row)
    safe_user.pop("password", None)
    return safe_user


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
        and len(database["orders"]) >= 500
        and len(database["policies"]) > 0
        and len(database["questions"]) == 500
    ):
        print("[PASS] DATABASE TEST PASSED!")
    else:
        print("[FAIL] DATABASE TEST FAILED!")
        print("Please check your CSV files.")

    print("=" * 50)