"""
SafeCart Final Enhancement & 13-Point Complete Verification Suite
Validates all requirements from the Final Enhancement specification:
1. Loading all available products and their categories
2. Product search and category filtering
3. Unique and correct images for different products (0 duplicates across database)
4. Valid and invalid Product ID lookup via Worker & Auditor AI
5. Valid, invalid, and unauthorized Order ID lookup with ownership verification
6. Add-to-cart, quantity changes, and item removal (Cart Validation API)
7. Stock validation and checkout
8. Demo-order creation and database persistence
9. Inventory updates after successful orders
10. Order confirmation and tracking
11. Worker Agent responses and Auditor Agent verification
12. Responsive design and Amazon Clone UI layout preservation
13. Existing features that must continue working
"""

import unittest
import sys
import pandas as pd
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from fastapi.testclient import TestClient
from Backend.main import app
import Database.database as db
from Backend.worker_agent import worker_agent
from Backend.auditor_agent import auditor_agent


class TestFinalEnhancements(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    # -------------------------------------------------------------------------
    # 1. Loading all available products and their categories
    # -------------------------------------------------------------------------
    def test_01_load_all_products_and_categories(self):
        res_prods = self.client.get("/api/products?limit=500")
        self.assertEqual(res_prods.status_code, 200)
        data = res_prods.json()
        self.assertEqual(data.get("status"), "SUCCESS")
        self.assertEqual(data.get("total"), 500)
        self.assertEqual(len(data.get("products")), 500)

        res_cats = self.client.get("/api/categories")
        self.assertEqual(res_cats.status_code, 200)
        cats = res_cats.json().get("categories", [])
        self.assertGreaterEqual(len(cats), 15)
        for expected in ["Electronics", "Clothing", "Mobiles", "Personal Care", "Furniture", "Home & Kitchen"]:
            self.assertIn(expected, cats)

    # -------------------------------------------------------------------------
    # 2. Product search and category filtering
    # -------------------------------------------------------------------------
    def test_02_product_search_and_category_filtering(self):
        res_search = self.client.get("/api/products?search=speaker")
        self.assertEqual(res_search.status_code, 200)
        search_items = res_search.json().get("products", [])
        self.assertTrue(any("speaker" in p["product_name"].lower() for p in search_items))

        res_cat = self.client.get("/api/products?category=Clothing&limit=500")
        self.assertEqual(res_cat.status_code, 200)
        clothing_items = res_cat.json().get("products", [])
        self.assertGreater(len(clothing_items), 0)
        self.assertTrue(all(p["category"] == "Clothing" for p in clothing_items))

    # -------------------------------------------------------------------------
    # 3. Unique and correct images for different products
    # -------------------------------------------------------------------------
    def test_03_unique_and_correct_product_images(self):
        products_df = pd.read_csv(PROJECT_ROOT / "Database" / "products.csv")
        self.assertEqual(len(products_df), 500)
        self.assertIn("image_url", products_df.columns)
        self.assertEqual(products_df["image_url"].isnull().sum(), 0)

        # Critical requirement: Every product has its own unique image (0 duplicates)
        unique_urls = products_df["image_url"].nunique()
        self.assertEqual(unique_urls, 500, f"Expected 500 unique URLs, got {unique_urls}")

        # Verify images differ across multiple categories
        sample_cats = ["Electronics", "Clothing", "Footwear", "Home & Kitchen", "Fitness"]
        cat_urls = set()
        for cat in sample_cats:
            cat_sample = products_df[products_df["category"] == cat].head(3)
            for _, row in cat_sample.iterrows():
                self.assertNotIn(row["image_url"], cat_urls)
                cat_urls.add(row["image_url"])

    # -------------------------------------------------------------------------
    # 4. Valid and invalid Product ID lookup
    # -------------------------------------------------------------------------
    def test_04_valid_and_invalid_product_id_lookup(self):
        # Valid Product ID: P001
        w_valid = worker_agent("P001", product_id="P001")
        self.assertEqual(w_valid["status"], "SUCCESS")
        self.assertEqual(w_valid["intent"], "PRODUCT_LOOKUP")
        self.assertIn("Wireless Headphones", w_valid["response"])
        self.assertIn("Rs. 1999", w_valid["response"])
        self.assertIn("Electronics", w_valid["response"])
        self.assertIn("image_url", w_valid["product"])

        a_valid = auditor_agent("P001", product_id="P001", worker_result=w_valid)
        self.assertEqual(a_valid["status"], "APPROVED")
        self.assertEqual(a_valid["audit_decision"], "APPROVED")

        # Invalid Product ID: P9999
        w_invalid = worker_agent("Product P9999")
        self.assertEqual(w_invalid["status"], "ERROR")
        self.assertEqual(w_invalid["intent"], "PRODUCT_LOOKUP")
        self.assertIn("was not found in the SafeCart database", w_invalid["response"])
        self.assertIn("valid Product ID", w_invalid["response"])

        a_invalid = auditor_agent("Product P9999", worker_result=w_invalid)
        self.assertEqual(a_invalid["status"], "ERROR")
        self.assertEqual(a_invalid["audit_decision"], "APPROVED")

    # -------------------------------------------------------------------------
    # 5. Valid, invalid, and unauthorized Order ID lookup
    # -------------------------------------------------------------------------
    def test_05_valid_invalid_and_unauthorized_order_id_lookup(self):
        # 1. Valid Order ID general lookup: O001
        w_ord = worker_agent("Order O001")
        self.assertEqual(w_ord["status"], "SUCCESS")
        self.assertEqual(w_ord["intent"], "ORDER_LOOKUP")
        self.assertIn("O001", w_ord["response"])
        self.assertIn("Product:", w_ord["response"])
        self.assertIn("Order Date:", w_ord["response"])
        self.assertIn("Delivery Date:", w_ord["response"])

        a_ord = auditor_agent("Order O001", worker_result=w_ord)
        self.assertEqual(a_ord["status"], "APPROVED")

        # 2. Invalid Order ID: O9999
        w_inv_ord = worker_agent("Order O9999")
        self.assertEqual(w_inv_ord["status"], "ERROR")
        self.assertEqual(w_inv_ord["intent"], "ORDER_LOOKUP")
        self.assertIn("was not found in the SafeCart database", w_inv_ord["response"])
        self.assertIn("valid Order ID", w_inv_ord["response"])

        a_inv_ord = auditor_agent("Order O9999", worker_result=w_inv_ord)
        self.assertEqual(a_inv_ord["status"], "ERROR")
        self.assertEqual(a_inv_ord["audit_decision"], "APPROVED")

        # 3. Unauthenticated request for private order information
        w_unauth = worker_agent("Show shipping address for O001")
        self.assertEqual(w_unauth["status"], "ERROR")
        self.assertTrue(w_unauth.get("requires_auth"))
        self.assertIn("Authentication required", w_unauth["response"])

        a_unauth = auditor_agent("Show shipping address for O001", worker_result=w_unauth)
        self.assertEqual(a_unauth["status"], "ERROR")
        self.assertEqual(a_unauth["audit_decision"], "APPROVED")

        # 4. Unauthorized cross-account access check
        # Order O500 belongs to customer@amazon.in
        w_wrong_user = worker_agent(
            "Show shipping address for O001",
            customer_name="Intruder User",
            customer_email="intruder@malicious.com",
            user_id="U999"
        )
        self.assertEqual(w_wrong_user["status"], "ERROR")
        self.assertTrue(w_wrong_user.get("unauthorized"))
        self.assertIn("Access denied", w_wrong_user["response"])

        a_wrong_user = auditor_agent(
            "Show shipping address for O001",
            worker_result=w_wrong_user,
            customer_name="Intruder User",
            customer_email="intruder@malicious.com"
        )
        self.assertEqual(a_wrong_user["status"], "ERROR")
        self.assertEqual(a_wrong_user["audit_decision"], "APPROVED")

    # -------------------------------------------------------------------------
    # 6. Add-to-cart, quantity changes, and item removal
    # -------------------------------------------------------------------------
    def test_06_cart_operations_and_validation(self):
        items = [
            {"product_id": "P001", "quantity": 3},
            {"product_id": "P002", "quantity": 2}
        ]
        res = self.client.post("/api/cart/validate", json=items)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "SUCCESS")
        # 1999 * 3 + 1499 * 2 = 5997 + 2998 = 8995
        self.assertEqual(data["subtotal"], 8995)
        self.assertTrue(data["all_available"])

        # Change quantity
        items[0]["quantity"] = 1
        res2 = self.client.post("/api/cart/validate", json=items)
        data2 = res2.json()
        self.assertEqual(data2["subtotal"], 1999 * 1 + 1499 * 2)

        # Remove item (only P002 remains)
        items_removed = [items[1]]
        res3 = self.client.post("/api/cart/validate", json=items_removed)
        data3 = res3.json()
        self.assertEqual(data3["subtotal"], 1499 * 2)

    # -------------------------------------------------------------------------
    # 7. Stock validation and checkout
    # -------------------------------------------------------------------------
    def test_07_stock_validation_and_checkout_error_on_oos(self):
        # Product P009 has 0 stock
        oos_payload = {
            "items": [{"product_id": "P009", "quantity": 1}],
            "customer_name": "Test User",
            "customer_email": "test@amazon.in"
        }
        res_fail = self.client.post("/api/checkout", json=oos_payload)
        self.assertEqual(res_fail.status_code, 400)
        self.assertIn("Insufficient stock", res_fail.json().get("message", ""))

    # -------------------------------------------------------------------------
    # 8. Demo-order creation and database persistence
    # -------------------------------------------------------------------------
    def test_08_demo_order_creation_and_persistence(self):
        # Pick product P006
        prod = db.get_product_with_inventory("P006")
        if prod["quantity"] < 2:
            db.set_inventory("P006", 20)

        payload = {
            "items": [{"product_id": "P006", "quantity": 1}],
            "customer_name": "Bhushan Fulari",
            "customer_email": "bhushan@safecart.com",
            "shipping_address": "123 MG Road, Mumbai, India",
            "payment_method": "Simulated Demo Instant Payment",
            "is_demo": True
        }
        res = self.client.post("/api/checkout", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "SUCCESS")
        self.assertTrue(data.get("demo_mode"))
        orders = data["orders"]
        self.assertEqual(len(orders), 1)

        new_oid = orders[0]["order_id"]
        self.assertTrue(new_oid.startswith("O"))

        # Verify saved in orders.csv
        persisted = db.find_order(new_oid)
        self.assertIsNotNone(persisted)
        self.assertEqual(persisted["product_id"], "P006")
        self.assertEqual(persisted["customer_name"], "Bhushan Fulari")
        self.assertEqual(persisted["customer_email"], "bhushan@safecart.com")

    # -------------------------------------------------------------------------
    # 9. Inventory updates after successful orders
    # -------------------------------------------------------------------------
    def test_09_inventory_decrement_after_order(self):
        prod = db.get_product_with_inventory("P008")
        current_qty = prod["quantity"]
        if current_qty < 5:
            db.set_inventory("P008", 20)
            current_qty = 20

        payload = {
            "product_id": "P008",
            "quantity": 2,
            "customer_name": "Stock Tester"
        }
        res = self.client.post("/api/orders", json=payload)
        self.assertEqual(res.status_code, 200)

        prod_after = db.get_product_with_inventory("P008")
        self.assertEqual(prod_after["quantity"], current_qty - 2)

    # -------------------------------------------------------------------------
    # 10. Order confirmation and tracking
    # -------------------------------------------------------------------------
    def test_10_order_confirmation_and_tracking(self):
        res = self.client.get("/api/orders/O001")
        self.assertEqual(res.status_code, 200)
        order = res.json().get("order")
        self.assertEqual(order["order_id"], "O001")
        self.assertEqual(order["product_id"], "P001")
        self.assertIn("delivery_date", order)
        self.assertIn("product_name", order)
        self.assertIn("price", order)

    # -------------------------------------------------------------------------
    # 11. Worker Agent responses and Auditor Agent verification
    # -------------------------------------------------------------------------
    def test_11_worker_and_auditor_compliance_rules(self):
        # Auditor catches invented price
        hallucinated_worker = {
            "status": "SUCCESS",
            "intent": "PRICE",
            "response": "The price of Wireless Headphones is Rs. 99.",
            "database_verified": True
        }
        audit = auditor_agent(
            "What is the price of P001?",
            product_id="P001",
            worker_result=hallucinated_worker
        )
        self.assertEqual(audit["audit_decision"], "CORRECTED")
        self.assertIn("1999", audit["response"])

    # -------------------------------------------------------------------------
    # 12. Responsive design and layout preservation
    # -------------------------------------------------------------------------
    def test_12_responsive_design_and_layout(self):
        html_file = PROJECT_ROOT / "amazon clone" / "Amazon.html"
        content = html_file.read_text(encoding="utf-8")
        self.assertIn("viewport", content)
        self.assertIn("navbar", content)
        self.assertIn("nav-search", content)
        self.assertIn("safecart-chat-widget", content)

        css_file = PROJECT_ROOT / "amazon clone" / "style.css"
        css_content = css_file.read_text(encoding="utf-8")
        self.assertIn("@media", css_content)
        self.assertIn(".chat-product-minicard", css_content)

    # -------------------------------------------------------------------------
    # 13. Existing features continue working
    # -------------------------------------------------------------------------
    def test_13_existing_features_continue_working(self):
        # Health
        res_health = self.client.get("/health")
        self.assertEqual(res_health.status_code, 200)
        # Policies
        res_pol = self.client.get("/api/policies")
        self.assertEqual(res_pol.status_code, 200)
        # Users
        res_usr = self.client.get("/api/users")
        self.assertEqual(res_usr.status_code, 200)
        self.assertGreaterEqual(len(res_usr.json().get("users", [])), 5)


if __name__ == "__main__":
    unittest.main()
