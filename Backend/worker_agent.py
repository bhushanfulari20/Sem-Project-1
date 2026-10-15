import re
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
        is_search_query,
        is_cart_query,
        is_checkout_query,
        is_product_id_query,
        is_order_id_query,
        is_private_order_query,
        extract_product_id,
        extract_order_id,
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
        is_search_query,
        is_cart_query,
        is_checkout_query,
        is_product_id_query,
        is_order_id_query,
        is_private_order_query,
        extract_product_id,
        extract_order_id,
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
# SEARCH CATALOG
# ============================================================

def search_catalog(search_term, limit=5):
    products = load_csv(PRODUCTS_FILE)
    if products.empty:
        return []
    inventory = load_csv(INVENTORY_FILE)
    inv_map = {}
    if not inventory.empty:
        for _, row in inventory.iterrows():
            inv_map[str(row["product_id"]).upper()] = int(row["quantity"])

    st = str(search_term).strip().lower()
    mask = (
        products["product_id"].astype(str).str.lower().str.contains(st, regex=False)
        | products["product_name"].astype(str).str.lower().str.contains(st, regex=False)
        | products["category"].astype(str).str.lower().str.contains(st, regex=False)
        | products["description"].astype(str).str.lower().str.contains(st, regex=False)
    )
    matches = products[mask]
    results = []
    for _, row in matches.head(limit).iterrows():
        d = row.to_dict()
        qty = inv_map.get(str(d["product_id"]).upper(), 0)
        d["quantity"] = qty
        d["in_stock"] = qty > 0
        results.append(d)
    return results


# ============================================================
# WORKER AGENT
# ============================================================

def worker_agent(
    query,
    order_id=None,
    product_id=None,
    customer_name=None,
    user_id=None,
    customer_email=None
):

    query = str(query).strip()

    # Extract Product ID from query if not explicitly passed
    if not product_id:
        m_prod = re.search(r'\b(P\d{3,4})\b', query, re.IGNORECASE)
        if m_prod:
            product_id = m_prod.group(1).upper()
        else:
            q_lower = query.lower()
            prods = load_csv(PRODUCTS_FILE)
            if not prods.empty and "product_name" in prods.columns:
                for _, row in prods.sort_values(by="product_name", key=lambda col: col.str.len(), ascending=False).iterrows():
                    p_name = str(row["product_name"]).strip()
                    if p_name and len(p_name) > 2 and p_name.lower() in q_lower:
                        product_id = str(row["product_id"]).upper()
                        break

    # Extract Order ID from query if not explicitly passed
    if not order_id:
        m_ord = re.search(r'\b(O\d{3,4})\b', query, re.IGNORECASE)
        if m_ord:
            order_id = m_ord.group(1).upper()


    # ========================================================
    # PRIVATE ORDER DETAILS (Authentication & Ownership Gate)
    # ========================================================

    if is_private_order_query(query):
        if not order_id:
            return {
                "status": "ERROR",
                "intent": "ORDER_LOOKUP",
                "response": "Please provide a valid Order ID.",
                "database_verified": False
            }

        order = find_order(order_id)
        if order is None:
            return {
                "status": "ERROR",
                "intent": "ORDER_LOOKUP",
                "response": f"Order {order_id} was not found in the SafeCart database. Please provide a valid Order ID.",
                "order_id": order_id,
                "database_verified": False
            }

        caller_name = str(customer_name or "").strip().lower()
        caller_email = str(customer_email or "").strip().lower()
        caller_id = str(user_id or "").strip().lower()
        is_authenticated = bool(caller_name or caller_email or caller_id)

        # Gate 1: Require authentication
        if not is_authenticated:
            return {
                "status": "ERROR",
                "intent": "ORDER_LOOKUP",
                "response": f"Authentication required: Please sign in to verify your identity and access private order details for {order_id}.",
                "order_id": order_id,
                "requires_auth": True,
                "database_verified": True
            }

        # Gate 2: Verify order ownership
        order_owner_email = str(order.get("customer_email", "")).strip().lower()
        if order_owner_email and caller_email and order_owner_email != caller_email:
            return {
                "status": "ERROR",
                "intent": "ORDER_LOOKUP",
                "response": f"Access denied: Order {order_id} does not belong to your verified account ({customer_email}). You can only view orders placed from your own account.",
                "order_id": order_id,
                "unauthorized": True,
                "database_verified": True
            }

        # Retrieve verified details
        pid = order.get("product_id")
        prod = find_product(pid) if pid else None
        p_name = prod.get("product_name", "SafeCart Item") if prod else "SafeCart Item"
        o_date = order.get("order_date", "N/A")
        d_date = order.get("delivery_date", "N/A")
        addr = order.get("shipping_address", "Registered Customer Address")
        pm = order.get("payment_method", "Simulated Demo Payment")
        c_name = order.get("customer_name", customer_name or "Amazon Customer")

        response = (
            f"Verified Order Details for {order_id}:\n"
            f"• Product: {p_name} ({pid})\n"
            f"• Customer: {c_name}\n"
            f"• Order Date: {o_date}\n"
            f"• Delivery Date: {d_date}\n"
            f"• Shipping Address: {addr}\n"
            f"• Payment Method: {pm}"
        )

        return {
            "status": "SUCCESS",
            "intent": "ORDER_LOOKUP",
            "response": response,
            "order": order,
            "product": prod,
            "database_verified": True
        }


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
    # CHECKOUT / PLACE ORDER
    # ========================================================

    if is_checkout_query(query):
        product = find_product(product_id)
        if product is None:
            return {
                "status": "ERROR",
                "intent": "PLACE_ORDER",
                "response": "Please provide a valid Product ID to place an order.",
                "database_verified": False
            }

        inventory = find_inventory(product_id)
        quantity = int(inventory.get("quantity", 0)) if inventory else 0

        if quantity <= 0:
            return {
                "status": "ERROR",
                "intent": "PLACE_ORDER",
                "response": f"The product {product.get('product_name')} is currently out of stock and cannot be ordered.",
                "product": product,
                "database_verified": True
            }

        price = product.get("price")
        product_name = product.get("product_name")
        response = (
            f"Ready to place order for {product_name} at verified price Rs. {price}. "
            f"Available quantity in stock: {quantity}. Please confirm your order."
        )

        return {
            "status": "SUCCESS",
            "intent": "PLACE_ORDER",
            "response": response,
            "product": product,
            "inventory": inventory,
            "database_verified": True
        }


    # ========================================================
    # CART (ADD / VIEW)
    # ========================================================

    if is_cart_query(query):
        q_lower = query.lower()
        if "view" in q_lower or "show" in q_lower or "my cart" in q_lower or "open" in q_lower:
            return {
                "status": "SUCCESS",
                "intent": "VIEW_CART",
                "response": "Here is your SafeCart shopping cart. You can review items, prices, and proceed to secure checkout.",
                "action": "VIEW_CART",
                "database_verified": True
            }

        product = find_product(product_id)
        if product is None:
            return {
                "status": "ERROR",
                "intent": "ADD_TO_CART",
                "response": "Please provide a valid Product ID to add to cart.",
                "database_verified": False
            }

        inventory = find_inventory(product_id)
        quantity = int(inventory.get("quantity", 0)) if inventory else 0

        if quantity <= 0:
            return {
                "status": "ERROR",
                "intent": "ADD_TO_CART",
                "response": f"The product {product.get('product_name')} is currently out of stock and cannot be added to cart.",
                "product": product,
                "database_verified": True
            }

        product_name = product.get("product_name")
        price = product.get("price")
        response = (
            f"Added {product_name} to your cart at verified price Rs. {price}! "
            f"Current stock: {quantity} units available."
        )

        return {
            "status": "SUCCESS",
            "intent": "ADD_TO_CART",
            "response": response,
            "product": product,
            "inventory": inventory,
            "action": "ADD_TO_CART",
            "database_verified": True
        }


    # ========================================================
    # PRODUCT ID LOOKUP
    # ========================================================

    if is_product_id_query(query) or (product_id and query.strip().upper() == str(product_id).strip().upper()):
        if not product_id:
            product_id = extract_product_id(query)

        product = find_product(product_id)
        if product is None:
            return {
                "status": "ERROR",
                "intent": "PRODUCT_LOOKUP",
                "response": f"Product {product_id} was not found in the SafeCart database. Please provide a valid Product ID.",
                "product_id": product_id,
                "database_verified": False
            }

        inv = find_inventory(product_id)
        quantity = int(inv.get("quantity", 0)) if inv else 0
        in_stock_str = f"In Stock ({quantity} units available)" if quantity > 0 else "Out of Stock (0 units available)"
        img_url = str(product.get("image_url", "")).strip()
        desc = str(product.get("description", "No description available.")).strip()
        p_name = product.get("product_name")
        p_cat = product.get("category")
        p_price = product.get("price")

        response = (
            f"Product {product_id} found in SafeCart database:\n"
            f"• Name: {p_name}\n"
            f"• Category: {p_cat}\n"
            f"• Price: Rs. {p_price}\n"
            f"• Stock: {in_stock_str}\n"
            f"• Description: {desc}"
        )

        return {
            "status": "SUCCESS",
            "intent": "PRODUCT_LOOKUP",
            "response": response,
            "product": {
                **product,
                "quantity": quantity,
                "in_stock": quantity > 0,
                "image_url": img_url
            },
            "inventory": inv,
            "database_verified": True
        }


    # ========================================================
    # ORDER ID LOOKUP
    # ========================================================

    if is_order_id_query(query) or is_private_order_query(query) or (order_id and query.strip().upper() == str(order_id).strip().upper()):
        if not order_id:
            order_id = extract_order_id(query)

        if not order_id:
            return {
                "status": "ERROR",
                "intent": "ORDER_LOOKUP",
                "response": "Please provide a valid Order ID.",
                "database_verified": False
            }

        order = find_order(order_id)
        if order is None:
            return {
                "status": "ERROR",
                "intent": "ORDER_LOOKUP",
                "response": f"Order {order_id} was not found in the SafeCart database. Please provide a valid Order ID.",
                "order_id": order_id,
                "database_verified": False
            }

        asking_private = is_private_order_query(query)
        caller_name = str(customer_name or "").strip().lower()
        caller_email = str(customer_email or "").strip().lower()
        caller_id = str(user_id or "").strip().lower()
        is_authenticated = bool(caller_name or caller_email or caller_id)

        order_owner_email = str(order.get("customer_email", "")).strip().lower()

        # Check authentication requirement for private order details
        if asking_private and not is_authenticated:
            return {
                "status": "ERROR",
                "intent": "ORDER_LOOKUP",
                "response": f"Authentication required: Please sign in to verify your identity and access private order details for {order_id}.",
                "order_id": order_id,
                "requires_auth": True,
                "database_verified": True
            }

        # Check ownership verification if order has an assigned owner
        if order_owner_email and caller_email and order_owner_email != caller_email:
            return {
                "status": "ERROR",
                "intent": "ORDER_LOOKUP",
                "response": f"Access denied: Order {order_id} does not belong to your verified account ({customer_email}). You can only view orders placed from your own account.",
                "order_id": order_id,
                "unauthorized": True,
                "database_verified": True
            }

        pid = order.get("product_id")
        prod = find_product(pid) if pid else None
        p_name = prod.get("product_name", "SafeCart Item") if prod else "SafeCart Item"
        o_date = order.get("order_date", "N/A")
        d_date = order.get("delivery_date", "N/A")
        refundable_status = str(order.get("refundable", "No")).capitalize()
        refunded_status = str(order.get("refunded", "No")).capitalize()

        from datetime import datetime
        try:
            today_str = datetime.now().strftime("%Y-%m-%d")
            status_text = "Delivered" if str(d_date) <= today_str else f"In Transit (Expected by {d_date})"
        except Exception:
            status_text = "In Transit"

        response = (
            f"Order {order_id} Details:\n"
            f"• Product: {p_name} ({pid})\n"
            f"• Order Date: {o_date}\n"
            f"• Delivery Date: {d_date}\n"
            f"• Current Status: {status_text}\n"
            f"• Refund Eligible: {refundable_status}\n"
            f"• Refunded: {refunded_status}"
        )

        if asking_private and is_authenticated:
            addr = order.get("shipping_address", "Registered Delivery Address")
            pm = order.get("payment_method", "Simulated Payment")
            c_name = order.get("customer_name", customer_name or "Amazon Customer")
            response += f"\n• Customer: {c_name}\n• Shipping Address: {addr}\n• Payment Method: {pm}"

        return {
            "status": "SUCCESS",
            "intent": "ORDER_LOOKUP",
            "response": response,
            "order": order,
            "product": prod,
            "database_verified": True
        }


    # ========================================================
    # SEARCH CATALOG
    # ========================================================

    if is_search_query(query):
        search_term = query
        for prefix in ["search for", "search", "find product", "find item", "show me products", "show products", "browse", "recommend", "do you have"]:
            if search_term.lower().startswith(prefix):
                search_term = search_term[len(prefix):].strip()
                break

        search_term = search_term.strip(" ?.!\"'")
        items = search_catalog(search_term if search_term else query, limit=5)

        if items:
            item_list = ", ".join([f"{p['product_name']} (Rs. {p['price']})" for p in items[:3]])
            response = f"Found {len(items)} matching products in catalog: {item_list}."
            return {
                "status": "SUCCESS",
                "intent": "SEARCH",
                "response": response,
                "products": items,
                "database_verified": True
            }
        else:
            return {
                "status": "SUCCESS",
                "intent": "SEARCH",
                "response": f"No products found matching '{search_term}'. You can search across Electronics, Accessories, Clothing, and more.",
                "products": [],
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