import pandas as pd
from pathlib import Path


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
    if not product_id:
        return None

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
    if not order_id:
        return None

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
    if not product_id:
        return None

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
# AUDITOR AGENT
# ============================================================

def auditor_agent(
    query,
    order_id=None,
    product_id=None,
    worker_result=None,
    customer_name=None,
    user_id=None,
    customer_email=None
):
    import re
    if not product_id:
        m_prod = re.search(r'\b(P\d{3,4})\b', str(query), re.IGNORECASE)
        if m_prod:
            product_id = m_prod.group(1).upper()
        else:
            q_lower = str(query).lower()
            prods = load_csv(PRODUCTS_FILE)
            if not prods.empty and "product_name" in prods.columns:
                for _, row in prods.sort_values(by="product_name", key=lambda col: col.str.len(), ascending=False).iterrows():
                    p_name = str(row["product_name"]).strip()
                    if p_name and len(p_name) > 2 and p_name.lower() in q_lower:
                        product_id = str(row["product_id"]).upper()
                        break

    if not order_id:
        m_ord = re.search(r'\b(O\d{3,4})\b', str(query), re.IGNORECASE)
        if m_ord:
            order_id = m_ord.group(1).upper()

    # --------------------------------------------------------
    # Check Worker Result
    # --------------------------------------------------------

    if worker_result is None:
        return {
            "status": "ERROR",
            "response": "Worker Agent did not provide a response.",
            "audit_decision": "REJECTED",
            "errors": ["Missing Worker Agent result"],
            "corrections": [],
            "correction_attempts": 0
        }

    intent = worker_result.get(
        "intent",
        "GENERAL"
    )

    worker_response = worker_result.get(
        "response",
        ""
    )

    worker_status = worker_result.get(
        "status",
        "SUCCESS"
    )

    # ========================================================
    # REFUND
    # ========================================================

    if intent == "REFUND":
        order = find_order(order_id)

        if order is None:
            return {
                "status": "ERROR",
                "response": "Please provide a valid Order ID.",
                "audit_decision": "REJECTED",
                "errors": ["Order not found in database"],
                "corrections": [],
                "correction_attempts": 1
            }

        refundable = str(order.get("refundable", "No")).strip().lower()
        refunded = str(order.get("refunded", "No")).strip().lower()

        if refunded == "yes":
            correct_response = f"Order {order_id} has already been refunded."
            is_accurate = ("already been refunded" in worker_response.lower() or "refunded" in worker_response.lower()) and "not eligible" not in worker_response.lower() and "is eligible for a refund" not in worker_response.lower()
        elif refundable == "yes":
            correct_response = (
                f"Order {order_id} is eligible for a refund according to the available return policy."
            )
            is_accurate = "eligible" in worker_response.lower() and "not eligible" not in worker_response.lower() and "already been refunded" not in worker_response.lower()
        else:
            correct_response = (
                f"Order {order_id} is not eligible for a refund according to the available database information."
            )
            is_accurate = "not eligible" in worker_response.lower() and "is eligible" not in worker_response.lower().replace("not eligible", "")

        if worker_status == "SUCCESS" and is_accurate:
            return {
                "status": "APPROVED",
                "response": worker_response,
                "audit_decision": "APPROVED",
                "errors": [],
                "corrections": [],
                "correction_attempts": 0
            }
        else:
            return {
                "status": "CORRECTED",
                "response": correct_response,
                "audit_decision": "CORRECTED",
                "errors": ["Worker refund statement mismatched database records"],
                "corrections": [f"Corrected refund response for order {order_id}"],
                "correction_attempts": 1
            }

    # ========================================================
    # RETURN
    # ========================================================

    if intent == "RETURN":
        order = find_order(order_id)

        if order is None:
            return {
                "status": "ERROR",
                "response": "Please provide a valid Order ID.",
                "audit_decision": "REJECTED",
                "errors": ["Order not found in database"],
                "corrections": [],
                "correction_attempts": 1
            }

        refundable = str(order.get("refundable", "No")).strip().lower()

        if refundable == "yes":
            correct_response = (
                f"Order {order_id} is eligible for return according to the available return information."
            )
            is_accurate = "eligible for return" in worker_response.lower() and "not eligible" not in worker_response.lower()
        else:
            correct_response = (
                f"Order {order_id} is not eligible for return according to the available database information."
            )
            is_accurate = "not eligible for return" in worker_response.lower()

        if worker_status == "SUCCESS" and is_accurate:
            return {
                "status": "APPROVED",
                "response": worker_response,
                "audit_decision": "APPROVED",
                "errors": [],
                "corrections": [],
                "correction_attempts": 0
            }
        else:
            return {
                "status": "CORRECTED",
                "response": correct_response,
                "audit_decision": "CORRECTED",
                "errors": ["Worker return statement mismatched database records"],
                "corrections": [f"Corrected return response for order {order_id}"],
                "correction_attempts": 1
            }

    # ========================================================
    # DELIVERY
    # ========================================================

    if intent == "DELIVERY":
        order = find_order(order_id)

        if order is None:
            return {
                "status": "ERROR",
                "response": "Please provide a valid Order ID.",
                "audit_decision": "REJECTED",
                "errors": ["Order not found in database"],
                "corrections": [],
                "correction_attempts": 1
            }

        delivery_date = str(order.get("delivery_date", "Not available")).strip()
        correct_response = f"The expected delivery date for order {order_id} is {delivery_date}."

        is_accurate = delivery_date != "Not available" and delivery_date in worker_response

        if worker_status == "SUCCESS" and is_accurate:
            return {
                "status": "APPROVED",
                "response": worker_response,
                "audit_decision": "APPROVED",
                "errors": [],
                "corrections": [],
                "correction_attempts": 0
            }
        else:
            return {
                "status": "CORRECTED",
                "response": correct_response,
                "audit_decision": "CORRECTED",
                "errors": ["Worker delivery date mismatched database records"],
                "corrections": [f"Corrected delivery date to {delivery_date}"],
                "correction_attempts": 1
            }

    # ========================================================
    # ORDER STATUS
    # ========================================================

    if intent == "ORDER_STATUS":
        order = find_order(order_id)

        if order is None:
            return {
                "status": "ERROR",
                "response": "Please provide a valid Order ID.",
                "audit_decision": "REJECTED",
                "errors": ["Order not found in database"],
                "corrections": [],
                "correction_attempts": 1
            }

        order_date = str(order.get("order_date", "Not available")).strip()
        delivery_date = str(order.get("delivery_date", "Not available")).strip()

        correct_response = (
            f"Order {order_id} was placed on {order_date} and the expected delivery date is {delivery_date}."
        )

        is_accurate = (
            (order_date in worker_response or order_date == "Not available")
            and (delivery_date in worker_response or delivery_date == "Not available")
        )

        if worker_status == "SUCCESS" and is_accurate:
            return {
                "status": "APPROVED",
                "response": worker_response,
                "audit_decision": "APPROVED",
                "errors": [],
                "corrections": [],
                "correction_attempts": 0
            }
        else:
            return {
                "status": "CORRECTED",
                "response": correct_response,
                "audit_decision": "CORRECTED",
                "errors": ["Worker order status mismatched database records"],
                "corrections": [f"Corrected order status for {order_id}"],
                "correction_attempts": 1
            }

    # ========================================================
    # INVENTORY
    # ========================================================

    if intent == "INVENTORY":
        inventory = find_inventory(product_id)

        if inventory is None:
            return {
                "status": "ERROR",
                "response": "Please provide a valid Product ID.",
                "audit_decision": "REJECTED",
                "errors": ["Product inventory not found in database"],
                "corrections": [],
                "correction_attempts": 1
            }

        quantity = int(inventory.get("quantity", 0))

        if quantity > 0:
            correct_response = f"The product is currently in stock. Available quantity: {quantity}."
            is_accurate = "in stock" in worker_response.lower() and "out of stock" not in worker_response.lower() and str(quantity) in worker_response
        else:
            correct_response = "The product is currently out of stock."
            is_accurate = "out of stock" in worker_response.lower() and "currently in stock" not in worker_response.lower()

        if worker_status == "SUCCESS" and is_accurate:
            return {
                "status": "APPROVED",
                "response": worker_response,
                "audit_decision": "APPROVED",
                "errors": [],
                "corrections": [],
                "correction_attempts": 0
            }
        else:
            return {
                "status": "CORRECTED",
                "response": correct_response,
                "audit_decision": "CORRECTED",
                "errors": ["Worker stock quantity or availability mismatched database records"],
                "corrections": [f"Corrected stock availability for {product_id}"],
                "correction_attempts": 1
            }

    # ========================================================
    # PRICE
    # ========================================================

    if intent == "PRICE":
        product = find_product(product_id)

        if product is None:
            return {
                "status": "ERROR",
                "response": "Please provide a valid Product ID.",
                "audit_decision": "REJECTED",
                "errors": ["Product not found in database"],
                "corrections": [],
                "correction_attempts": 1
            }

        product_name = str(product.get("product_name", "Product")).strip()
        price = str(product.get("price", "Not available")).strip()

        correct_response = f"The price of {product_name} is Rs. {price}."

        is_accurate = (
            str(price) != "Not available"
            and str(price) in worker_response
            and (product_name.lower() in worker_response.lower() or "product" in worker_response.lower())
        )

        if worker_status == "SUCCESS" and is_accurate:
            return {
                "status": "APPROVED",
                "response": worker_response,
                "audit_decision": "APPROVED",
                "errors": [],
                "corrections": [],
                "correction_attempts": 0
            }
        else:
            return {
                "status": "CORRECTED",
                "response": correct_response,
                "audit_decision": "CORRECTED",
                "errors": [f"Worker price mismatched database price of Rs. {price}"],
                "corrections": [f"Corrected price to Rs. {price}"],
                "correction_attempts": 1
            }

    # ========================================================
    # PRODUCT INFORMATION
    # ========================================================

    if intent == "PRODUCT_INFO":
        product = find_product(product_id)

        if product is None:
            return {
                "status": "ERROR",
                "response": "Please provide a valid Product ID.",
                "audit_decision": "REJECTED",
                "errors": ["Product not found in database"],
                "corrections": [],
                "correction_attempts": 1
            }

        product_name = str(product.get("product_name", "Product")).strip()
        category = str(product.get("category", "Not available")).strip()
        description = str(product.get("description", "Not available")).strip()

        correct_response = f"{product_name} is in the {category} category. {description}"

        is_accurate = (
            product_name.lower() in worker_response.lower()
            and (category.lower() in worker_response.lower() or category == "Not available")
        )

        if worker_status == "SUCCESS" and is_accurate:
            return {
                "status": "APPROVED",
                "response": worker_response,
                "audit_decision": "APPROVED",
                "errors": [],
                "corrections": [],
                "correction_attempts": 0
            }
        else:
            return {
                "status": "CORRECTED",
                "response": correct_response,
                "audit_decision": "CORRECTED",
                "errors": ["Worker product details mismatched database records"],
                "corrections": [f"Corrected product information for {product_id}"],
                "correction_attempts": 1
            }

    # ========================================================
    # CANCELLATION
    # ========================================================

    if intent == "CANCELLATION":
        order = find_order(order_id)

        if order is None:
            return {
                "status": "ERROR",
                "response": "Please provide a valid Order ID.",
                "audit_decision": "REJECTED",
                "errors": ["Order not found in database"],
                "corrections": [],
                "correction_attempts": 1
            }

        refundable = str(order.get("refundable", "No")).strip().lower()

        if refundable == "yes":
            correct_response = (
                f"Cancellation request received for order {order_id}. "
                "Please verify the order before processing the cancellation."
            )
            is_accurate = "cancellation request received" in worker_response.lower()
        else:
            correct_response = (
                f"Order {order_id} cannot be confirmed for cancellation using the available database information."
            )
            is_accurate = "cannot be confirmed" in worker_response.lower()

        if worker_status == "SUCCESS" and is_accurate:
            return {
                "status": "APPROVED",
                "response": worker_response,
                "audit_decision": "APPROVED",
                "errors": [],
                "corrections": [],
                "correction_attempts": 0
            }
        else:
            return {
                "status": "CORRECTED",
                "response": correct_response,
                "audit_decision": "CORRECTED",
                "errors": ["Worker cancellation response mismatched order status"],
                "corrections": [f"Corrected cancellation response for order {order_id}"],
                "correction_attempts": 1
            }

    # ========================================================
    # POLICY
    # ========================================================

    if intent == "POLICY":
        policies = load_csv(POLICIES_FILE)

        if policies.empty:
            return {
                "status": "ERROR",
                "response": "Policy information is not available.",
                "audit_decision": "REJECTED",
                "errors": ["Policy database is empty"],
                "corrections": [],
                "correction_attempts": 1
            }

        policy = policies.iloc[0].to_dict()
        policy_type = policy.get("policy_type", "Policy")
        policy_details = policy.get("policy_details", "Not available")

        correct_response = f"{policy_type}: {policy_details}"

        if worker_status == "SUCCESS" and worker_response:
            return {
                "status": "APPROVED",
                "response": worker_response,
                "audit_decision": "APPROVED",
                "errors": [],
                "corrections": [],
                "correction_attempts": 0
            }
        else:
            return {
                "status": "CORRECTED",
                "response": correct_response,
                "audit_decision": "CORRECTED",
                "errors": ["Worker policy statement required correction"],
                "corrections": ["Provided official policy details"],
                "correction_attempts": 1
            }

    # ========================================================
    # COMPLAINT
    # ========================================================

    if intent == "COMPLAINT":
        order = find_order(order_id)

        if order is None:
            return {
                "status": "ERROR",
                "response": "Please provide a valid Order ID.",
                "audit_decision": "REJECTED",
                "errors": ["Order not found in database"],
                "corrections": [],
                "correction_attempts": 1
            }

        if worker_status == "SUCCESS" and worker_response:
            return {
                "status": "APPROVED",
                "response": worker_response,
                "audit_decision": "APPROVED",
                "errors": [],
                "corrections": [],
                "correction_attempts": 0
            }
        else:
            correct_response = (
                f"We are sorry that you are experiencing a problem with order {order_id}. "
                "Your order was found in our database. Please contact customer support for further assistance."
            )
            return {
                "status": "CORRECTED",
                "response": correct_response,
                "audit_decision": "CORRECTED",
                "errors": ["Worker complaint handling required formatting"],
                "corrections": ["Applied standard customer support protocol"],
                "correction_attempts": 1
            }

    # ========================================================
    # CHECKOUT / PLACE ORDER
    # ========================================================

    if intent == "PLACE_ORDER":
        product = find_product(product_id)
        if product is None:
            return {
                "status": "ERROR",
                "response": "Please provide a valid Product ID to place an order.",
                "audit_decision": "REJECTED",
                "errors": ["Product not found in database for checkout"],
                "corrections": [],
                "correction_attempts": 1
            }

        inventory = find_inventory(product_id)
        quantity = int(inventory.get("quantity", 0)) if inventory else 0

        if quantity <= 0:
            correct_response = f"The product {product.get('product_name')} is currently out of stock and cannot be ordered."
            return {
                "status": "CORRECTED",
                "response": correct_response,
                "audit_decision": "CORRECTED",
                "errors": ["Worker proposed checkout for an out-of-stock product"],
                "corrections": [f"Blocked out-of-stock product {product_id} from checkout"],
                "correction_attempts": 1
            }

        price = str(product.get("price"))
        if price not in worker_response:
            correct_response = f"Ready to place order for {product.get('product_name')} at verified price Rs. {price}. Available quantity: {quantity}. Please confirm your order."
            return {
                "status": "CORRECTED",
                "response": correct_response,
                "audit_decision": "CORRECTED",
                "errors": [f"Worker price mismatched database price of Rs. {price}"],
                "corrections": [f"Calibrated price to Rs. {price}"],
                "correction_attempts": 1
            }

        return {
            "status": "APPROVED",
            "response": worker_response,
            "audit_decision": "APPROVED",
            "errors": [],
            "corrections": [],
            "correction_attempts": 0
        }

    # ========================================================
    # CART (ADD / VIEW)
    # ========================================================

    if intent == "ADD_TO_CART":
        product = find_product(product_id)
        if product is None:
            return {
                "status": "ERROR",
                "response": "Please provide a valid Product ID to add to cart.",
                "audit_decision": "REJECTED",
                "errors": ["Product not found in database"],
                "corrections": [],
                "correction_attempts": 1
            }

        inventory = find_inventory(product_id)
        quantity = int(inventory.get("quantity", 0)) if inventory else 0

        if quantity <= 0:
            correct_response = f"The product {product.get('product_name')} is currently out of stock and cannot be added to cart."
            return {
                "status": "CORRECTED",
                "response": correct_response,
                "audit_decision": "CORRECTED",
                "errors": ["Worker attempted to add out-of-stock product to cart"],
                "corrections": [f"Blocked out-of-stock product {product_id} from cart"],
                "correction_attempts": 1
            }

        price = str(product.get("price"))
        if price not in worker_response:
            correct_response = f"Added {product.get('product_name')} to your cart at verified price Rs. {price}! Current stock: {quantity} units available."
            return {
                "status": "CORRECTED",
                "response": correct_response,
                "audit_decision": "CORRECTED",
                "errors": [f"Worker price mismatched database price of Rs. {price}"],
                "corrections": [f"Calibrated price to Rs. {price}"],
                "correction_attempts": 1
            }

        return {
            "status": "APPROVED",
            "response": worker_response,
            "audit_decision": "APPROVED",
            "errors": [],
            "corrections": [],
            "correction_attempts": 0
        }

    if intent == "VIEW_CART":
        return {
            "status": "APPROVED",
            "response": worker_response,
            "audit_decision": "APPROVED",
            "errors": [],
            "corrections": [],
            "correction_attempts": 0
        }

    # ========================================================
    # SEARCH
    # ========================================================

    if intent == "SEARCH":
        products = worker_result.get("products", [])
        verified_products = []
        errors = []
        for p in products:
            pid = p.get("product_id")
            real_p = find_product(pid)
            if real_p and str(real_p.get("price")) == str(p.get("price")):
                verified_products.append(p)
            else:
                errors.append(f"Mismatched or unverified product: {pid}")

        if errors:
            item_list = ", ".join([f"{p['product_name']} (Rs. {p['price']})" for p in verified_products[:3]])
            calibrated_response = f"Found {len(verified_products)} verified products in catalog: {item_list}."
            return {
                "status": "CORRECTED",
                "response": calibrated_response,
                "audit_decision": "CORRECTED",
                "errors": errors,
                "corrections": ["Filtered search results to verified database catalog"],
                "correction_attempts": 1
            }

        return {
            "status": "APPROVED",
            "response": worker_response,
            "audit_decision": "APPROVED",
            "errors": [],
            "corrections": [],
            "correction_attempts": 0
        }

    # ========================================================
    # PRODUCT LOOKUP
    # ========================================================

    if intent == "PRODUCT_LOOKUP":
        if worker_status == "ERROR":
            real_product = find_product(product_id)
            if real_product is None:
                return {
                    "status": "ERROR",
                    "response": worker_response,
                    "audit_decision": "APPROVED",
                    "errors": [],
                    "corrections": [],
                    "correction_attempts": 0
                }
            else:
                inv = find_inventory(product_id)
                qty = int(inv.get("quantity", 0)) if inv else 0
                in_stock_str = f"In Stock ({qty} units available)" if qty > 0 else "Out of Stock (0 units available)"
                calibrated = (
                    f"Product {product_id} found in SafeCart database:\n"
                    f"• Name: {real_product.get('product_name')}\n"
                    f"• Category: {real_product.get('category')}\n"
                    f"• Price: Rs. {real_product.get('price')}\n"
                    f"• Stock: {in_stock_str}\n"
                    f"• Description: {real_product.get('description')}"
                )
                return {
                    "status": "CORRECTED",
                    "response": calibrated,
                    "audit_decision": "CORRECTED",
                    "errors": [f"Worker falsely reported product {product_id} as missing"],
                    "corrections": [f"Retrieved verified product {product_id} from database"],
                    "correction_attempts": 1
                }
        else:
            real_product = find_product(product_id)
            if real_product is None:
                return {
                    "status": "ERROR",
                    "response": f"Product {product_id} was not found in the SafeCart database. Please provide a valid Product ID.",
                    "audit_decision": "REJECTED",
                    "errors": [f"Worker invented non-existent product {product_id}"],
                    "corrections": ["Blocked hallucinated product"],
                    "correction_attempts": 1
                }

            real_price = str(real_product.get("price"))
            inv = find_inventory(product_id)
            real_qty = int(inv.get("quantity", 0)) if inv else 0

            errors = []
            corrections = []
            needs_calibration = False

            if real_price not in worker_response:
                errors.append(f"Worker price mismatched database price Rs. {real_price}")
                corrections.append(f"Calibrated price to Rs. {real_price}")
                needs_calibration = True

            if real_qty == 0 and "out of stock" not in worker_response.lower():
                errors.append(f"Worker claimed product in stock when database quantity is 0")
                corrections.append("Corrected stock status to out of stock")
                needs_calibration = True

            if needs_calibration:
                in_stock_str = f"In Stock ({real_qty} units available)" if real_qty > 0 else "Out of Stock (0 units available)"
                calibrated = (
                    f"Product {product_id} found in SafeCart database:\n"
                    f"• Name: {real_product.get('product_name')}\n"
                    f"• Category: {real_product.get('category')}\n"
                    f"• Price: Rs. {real_price}\n"
                    f"• Stock: {in_stock_str}\n"
                    f"• Description: {real_product.get('description')}"
                )
                return {
                    "status": "CORRECTED",
                    "response": calibrated,
                    "audit_decision": "CORRECTED",
                    "errors": errors,
                    "corrections": corrections,
                    "correction_attempts": 1
                }

            return {
                "status": "APPROVED",
                "response": worker_response,
                "audit_decision": "APPROVED",
                "errors": [],
                "corrections": [],
                "correction_attempts": 0
            }


    # ========================================================
    # ORDER LOOKUP
    # ========================================================

    if intent == "ORDER_LOOKUP":
        if worker_status == "ERROR":
            real_order = find_order(order_id)
            if real_order is None:
                return {
                    "status": "ERROR",
                    "response": worker_response,
                    "audit_decision": "APPROVED",
                    "errors": [],
                    "corrections": [],
                    "correction_attempts": 0
                }
            if worker_result.get("requires_auth") or worker_result.get("unauthorized"):
                return {
                    "status": "ERROR",
                    "response": worker_response,
                    "audit_decision": "APPROVED",
                    "errors": [],
                    "corrections": [],
                    "correction_attempts": 0
                }
            return {
                "status": "ERROR",
                "response": worker_response,
                "audit_decision": "APPROVED",
                "errors": [],
                "corrections": [],
                "correction_attempts": 0
            }
        else:
            real_order = find_order(order_id)
            if real_order is None:
                return {
                    "status": "ERROR",
                    "response": f"Order {order_id} was not found in the SafeCart database. Please provide a valid Order ID.",
                    "audit_decision": "REJECTED",
                    "errors": [f"Worker invented non-existent order {order_id}"],
                    "corrections": ["Blocked hallucinated order details"],
                    "correction_attempts": 1
                }

            real_delivery = str(real_order.get("delivery_date", ""))
            real_pid = str(real_order.get("product_id", ""))
            if real_delivery and real_delivery not in worker_response:
                return {
                    "status": "CORRECTED",
                    "response": f"Order {order_id} was placed for product {real_pid}. Expected delivery date is {real_delivery}.",
                    "audit_decision": "CORRECTED",
                    "errors": [f"Worker delivery date mismatched database: {real_delivery}"],
                    "corrections": [f"Calibrated delivery date to {real_delivery}"],
                    "correction_attempts": 1
                }

            return {
                "status": "APPROVED",
                "response": worker_response,
                "audit_decision": "APPROVED",
                "errors": [],
                "corrections": [],
                "correction_attempts": 0
            }


    # ========================================================
    # GENERAL
    # ========================================================

    if not worker_response:
        return {
            "status": "ERROR",
            "response": "SafeCart could not generate a valid response.",
            "audit_decision": "REJECTED",
            "errors": ["Empty Worker Agent response"],
            "corrections": [],
            "correction_attempts": 1
        }

    # ========================================================
    # APPROVE GENERAL RESPONSE
    # ========================================================

    return {
        "status": "APPROVED",
        "response": worker_response,
        "audit_decision": "APPROVED",
        "errors": [],
        "corrections": [],
        "correction_attempts": 0
    }