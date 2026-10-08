import pandas as pd
from pathlib import Path

try:
    from .rules import (
        is_refund_query,
        is_return_query,
        is_delivery_query,
        is_order_status_query,
        is_inventory_query,
        is_price_query,
        is_cancellation_query,
        is_product_info_query,
        is_policy_query,
        is_complaint_query,
    )
except ImportError:
    from rules import (
        is_refund_query,
        is_return_query,
        is_delivery_query,
        is_order_status_query,
        is_inventory_query,
        is_price_query,
        is_cancellation_query,
        is_product_info_query,
        is_policy_query,
        is_complaint_query,
    )


# ============================================================
# DATABASE PATH
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_DIR = BASE_DIR / "Database" if (BASE_DIR / "Database").is_dir() else BASE_DIR / "database"

PRODUCTS_FILE = DATABASE_DIR / "products.csv"
INVENTORY_FILE = DATABASE_DIR / "inventory.csv"
ORDERS_FILE = DATABASE_DIR / "orders.csv"
POLICIES_FILE = DATABASE_DIR / "policies.csv"


# ============================================================
# LOAD CSV
# ============================================================

def load_csv(file_path):

    try:
        return pd.read_csv(file_path)

    except FileNotFoundError:

        print(f"[ERROR] File not found: {file_path}")

        return pd.DataFrame()

    except Exception as e:

        print(f"[ERROR] Error loading {file_path}: {e}")

        return pd.DataFrame()


# ============================================================
# FIND PRODUCT
# ============================================================

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


# ============================================================
# FIND ORDER
# ============================================================

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


# ============================================================
# FIND INVENTORY
# ============================================================

def find_inventory(product_id):

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


# ============================================================
# FIND POLICY
# ============================================================

def find_policy(policy_keyword):

    policies = load_csv(POLICIES_FILE)

    if policies.empty:
        return None

    for _, row in policies.iterrows():

        policy_type = str(row.get("policy_type", "")).lower()
        policy_details = str(row.get("policy_details", "")).lower()

        if (
            policy_keyword.lower() in policy_type
            or policy_keyword.lower() in policy_details
        ):

            return row.to_dict()

    return None


# ============================================================
# WORKER AGENT
# ============================================================

def worker_agent(query, order_id=None, product_id=None):

    query = str(query).strip()


    # ========================================================
    # REFUND
    # ========================================================

    if is_refund_query(query):

        order = find_order(order_id)

        if order is None:

            return {
                "status": "ERROR",
                "intent": "REFUND",
                "response": "Please provide a valid Order ID.",
                "database_verified": False
            }

        refundable = str(
            order.get("refundable", "No")
        ).lower()

        refunded = str(
            order.get("refunded", "No")
        ).lower()

        if refunded == "yes":

            response = (
                f"Order {order_id} has already been refunded."
            )

        elif refundable == "yes":

            response = (
                f"Order {order_id} is eligible for a refund "
                "according to the available return policy."
            )

        else:

            response = (
                f"Order {order_id} is not eligible for a refund "
                "according to the available database information."
            )

        return {
            "status": "SUCCESS",
            "intent": "REFUND",
            "response": response,
            "order": order,
            "database_verified": True
        }


    # ========================================================
    # RETURN
    # ========================================================

    if is_return_query(query):

        order = find_order(order_id)

        if order is None:

            return {
                "status": "ERROR",
                "intent": "RETURN",
                "response": "Please provide a valid Order ID.",
                "database_verified": False
            }

        refundable = str(
            order.get("refundable", "No")
        ).lower()

        if refundable == "yes":

            response = (
                f"Order {order_id} is eligible for return "
                "according to the available return information."
            )

        else:

            response = (
                f"Order {order_id} is not eligible for return "
                "according to the available database information."
            )

        return {
            "status": "SUCCESS",
            "intent": "RETURN",
            "response": response,
            "order": order,
            "database_verified": True
        }


    # ========================================================
    # DELIVERY
    # ========================================================

    if is_delivery_query(query):

        order = find_order(order_id)

        if order is None:

            return {
                "status": "ERROR",
                "intent": "DELIVERY",
                "response": "Please provide a valid Order ID.",
                "database_verified": False
            }

        delivery_date = order.get(
            "delivery_date",
            "Not available"
        )

        response = (
            f"The expected delivery date for order "
            f"{order_id} is {delivery_date}."
        )

        return {
            "status": "SUCCESS",
            "intent": "DELIVERY",
            "response": response,
            "order": order,
            "database_verified": True
        }


    # ========================================================
    # ORDER STATUS
    # ========================================================

    if is_order_status_query(query):

        order = find_order(order_id)

        if order is None:

            return {
                "status": "ERROR",
                "intent": "ORDER_STATUS",
                "response": "Please provide a valid Order ID.",
                "database_verified": False
            }

        order_date = order.get(
            "order_date",
            "Not available"
        )

        delivery_date = order.get(
            "delivery_date",
            "Not available"
        )

        response = (
            f"Order {order_id} was placed on {order_date} "
            f"and the expected delivery date is {delivery_date}."
        )

        return {
            "status": "SUCCESS",
            "intent": "ORDER_STATUS",
            "response": response,
            "order": order,
            "database_verified": True
        }


    # ========================================================
    # INVENTORY / STOCK
    # ========================================================

    if is_inventory_query(query):

        inventory = find_inventory(product_id)

        if inventory is None:

            return {
                "status": "ERROR",
                "intent": "INVENTORY",
                "response": "Please provide a valid Product ID.",
                "database_verified": False
            }

        quantity = int(
            inventory.get("quantity", 0)
        )

        if quantity > 0:

            response = (
                f"The product is currently in stock. "
                f"Available quantity: {quantity}."
            )

        else:

            response = (
                "The product is currently out of stock."
            )

        return {
            "status": "SUCCESS",
            "intent": "INVENTORY",
            "response": response,
            "inventory": inventory,
            "database_verified": True
        }


    # ========================================================
    # PRICE
    # ========================================================

    if is_price_query(query):

        product = find_product(product_id)

        if product is None:

            return {
                "status": "ERROR",
                "intent": "PRICE",
                "response": "Please provide a valid Product ID.",
                "database_verified": False
            }

        product_name = product.get(
            "product_name",
            "Product"
        )

        price = product.get(
            "price",
            "Not available"
        )

        response = (
            f"The price of {product_name} is Rs. {price}."
        )

        return {
            "status": "SUCCESS",
            "intent": "PRICE",
            "response": response,
            "product": product,
            "database_verified": True
        }


    # ========================================================
    # PRODUCT INFORMATION
    # ========================================================

    if is_product_info_query(query):

        product = find_product(product_id)

        if product is None:

            return {
                "status": "ERROR",
                "intent": "PRODUCT_INFO",
                "response": "Please provide a valid Product ID.",
                "database_verified": False
            }

        product_name = product.get(
            "product_name",
            "Product"
        )

        category = product.get(
            "category",
            "Not available"
        )

        description = product.get(
            "description",
            "Not available"
        )

        response = (
            f"{product_name} is in the {category} category. "
            f"{description}"
        )

        return {
            "status": "SUCCESS",
            "intent": "PRODUCT_INFO",
            "response": response,
            "product": product,
            "database_verified": True
        }


    # ========================================================
    # CANCELLATION
    # ========================================================

    if is_cancellation_query(query):

        order = find_order(order_id)

        if order is None:

            return {
                "status": "ERROR",
                "intent": "CANCELLATION",
                "response": "Please provide a valid Order ID.",
                "database_verified": False
            }

        refundable = str(
            order.get("refundable", "No")
        ).lower()

        if refundable == "yes":

            response = (
                f"Cancellation request received for order {order_id}. "
                "Please verify the order before processing the cancellation."
            )

        else:

            response = (
                f"Order {order_id} cannot be confirmed for "
                "cancellation using the available database information."
            )

        return {
            "status": "SUCCESS",
            "intent": "CANCELLATION",
            "response": response,
            "order": order,
            "database_verified": True
        }


    # ========================================================
    # POLICY
    # ========================================================

    if is_policy_query(query):

        policy = find_policy("Policy")

        if policy is None:

            return {
                "status": "ERROR",
                "intent": "POLICY",
                "response": "Policy information is not available.",
                "database_verified": False
            }

        policy_type = policy.get(
            "policy_type",
            "Policy"
        )

        policy_details = policy.get(
            "policy_details",
            "Not available"
        )

        response = (
            f"{policy_type}: {policy_details}"
        )

        return {
            "status": "SUCCESS",
            "intent": "POLICY",
            "response": response,
            "policy": policy,
            "database_verified": True
        }


    # ========================================================
    # COMPLAINT
    # ========================================================

    if is_complaint_query(query):

        order = find_order(order_id)

        if order is None:

            return {
                "status": "ERROR",
                "intent": "COMPLAINT",
                "response": "Please provide a valid Order ID.",
                "database_verified": False
            }

        response = (
            f"We are sorry that you are experiencing a problem "
            f"with order {order_id}. Your order was found in our "
            "database. Please contact customer support for further "
            "assistance with the issue."
        )

        return {
            "status": "SUCCESS",
            "intent": "COMPLAINT",
            "response": response,
            "order": order,
            "database_verified": True
        }


    # ========================================================
    # GENERAL / UNKNOWN QUERY
    # ========================================================

    return {
        "status": "SUCCESS",
        "intent": "GENERAL",
        "response": (
            "I can help you with product information, "
            "price, stock availability, delivery, order status, "
            "returns, refunds, cancellations, policies, "
            "and complaints."
        ),
        "database_verified": False
    }


# ============================================================
# DIRECT TEST
# ============================================================

if __name__ == "__main__":

    print("=" * 60)
    print("             SafeCart Worker Agent Test")
    print("=" * 60)

    result = worker_agent(
        "What is the price of my product?",
        product_id="P001"
    )

    print(result)

    print("=" * 60)