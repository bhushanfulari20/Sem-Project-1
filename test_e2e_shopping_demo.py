"""
SafeCart Amazon Clone End-to-End Shopping Demo Test Suite
Validates the complete 11-step customer shopping journey:
1. Catalog: All 500 SafeCart products loaded category-wise with real prices and inventory.
2. Product Details: Product details view, price verification, stock checks.
3. Cart Operations: Add to cart, quantity update, stock limits, remove item, subtotal.
4. Checkout: Customer details, delivery address, simulated payment method, demo mode.
5. Demo Order Placement: Creates real order in Database/orders.csv with generated order ID (e.g. O501+).
6. Safe Inventory Decrement: Live inventory in Database/inventory.csv safely decremented.
7. Order Confirmation & Tracking: Order confirmation details, tracking API with timeline data.
8. SafeCart AI Chatbot: Worker Agent handles queries, Auditor Agent validates prices, stock, and policies.
9. Image Integrity: Verifies semantic image mapping without PID badges (e.g., Bluetooth Speaker shows speaker).
"""

import sys
import unittest
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from fastapi.testclient import TestClient
from Backend.main import app
import Database.database as db
from Backend.worker_agent import worker_agent
from Backend.auditor_agent import auditor_agent


class TestE2EShoppingDemo(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_step_01_browse_500_products_category_wise(self):
        """Step 1: Display all 500 products category-wise with prices and stock."""
        # 1. Fetch categories
        res_cats = self.client.get("/api/categories")
        self.assertEqual(res_cats.status_code, 200)
        categories = res_cats.json().get("categories", [])
        self.assertGreaterEqual(len(categories), 15)

        # 2. Fetch all products
        res_prods = self.client.get("/api/products?limit=500")
        self.assertEqual(res_prods.status_code, 200)
        data = res_prods.json()
        self.assertGreaterEqual(data.get("total"), 500)
        products = data.get("products", [])
        self.assertGreaterEqual(len(products), 500)

        # Verify each product has necessary attributes
        for p in products[:20]:
            self.assertIn("product_id", p)
            self.assertIn("product_name", p)
            self.assertIn("category", p)
            self.assertIn("price", p)
            self.assertIn("quantity", p)
            self.assertIn("in_stock", p)

        # Verify products can be partitioned category-wise
        by_category = {}
        for p in products:
            by_category.setdefault(p["category"], []).append(p)
        self.assertIn("Electronics", by_category)
        self.assertGreater(len(by_category["Electronics"]), 10)

    def test_step_02_product_details_and_stock(self):
        """Step 2: User opens product details and checks live price and inventory."""
        res = self.client.get("/api/products/P002")
        self.assertEqual(res.status_code, 200)
        p002 = res.json().get("product")
        self.assertEqual(p002["product_id"], "P002")
        self.assertEqual(p002["product_name"], "Bluetooth Speaker")
        self.assertEqual(p002["category"], "Electronics")
        self.assertEqual(p002["price"], 1499)
        self.assertGreaterEqual(p002["quantity"], 0)
        self.assertTrue(p002["in_stock"])

    def test_step_03_cart_validation_and_stock_limits(self):
        """Step 3: Add to cart, validate stock, calculate subtotal."""
        cart_items = [
            {"product_id": "P002", "quantity": 2},  # Bluetooth Speaker: 1499 * 2 = 2998
            {"product_id": "P003", "quantity": 1}   # Smart Watch: 2999 * 1 = 2999
        ]
        res = self.client.post("/api/cart/validate", json=cart_items)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data.get("status"), "SUCCESS")
        self.assertEqual(data.get("subtotal"), 2998 + 2999)
        self.assertTrue(data.get("all_available"))

    def test_step_04_and_05_checkout_and_place_demo_order(self):
        """Steps 4 & 5: Place demo order, generate real Order ID, update inventory safely."""
        # Pick test products with known stock
        prod_before = db.get_product_with_inventory("P006")
        initial_qty = prod_before["quantity"]
        self.assertGreater(initial_qty, 2)

        checkout_payload = {
            "items": [
                {"product_id": "P006", "quantity": 1}
            ],
            "customer_name": "Demo Shopper",
            "customer_email": "demo.shopper@safecart.com",
            "customer_phone": "+91 98765 12345",
            "shipping_address": "Suite 501, SafeCart Demo Tower, Mumbai, PIN: 400001",
            "payment_method": "Demo Instant Pay (Auto-Confirmed Simulation)",
            "is_demo": True
        }

        res = self.client.post("/api/checkout", json=checkout_payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data.get("status"), "SUCCESS")
        created_orders = data.get("orders", [])
        self.assertEqual(len(created_orders), 1)

        new_order = created_orders[0]
        self.assertTrue(new_order["order_id"].startswith("O"))
        self.assertEqual(new_order["product_id"], "P006")
        self.assertEqual(new_order["customer_name"], "Demo Shopper")
        self.assertIn("Suite 501", new_order["shipping_address"])

        # Step 5: Verify inventory decremented in database
        prod_after = db.get_product_with_inventory("P006")
        self.assertEqual(prod_after["quantity"], initial_qty - 1)

        # Restore inventory for repeatability
        db.update_inventory("P006", initial_qty)

    def test_step_06_order_confirmation_and_tracking(self):
        """Step 6: Track order via API with delivery date and status timeline."""
        # Query order O001
        res = self.client.get("/api/orders/O001")
        self.assertEqual(res.status_code, 200)
        order = res.json().get("order")
        self.assertEqual(order["order_id"], "O001")
        self.assertEqual(order["product_id"], "P001")
        self.assertIn("delivery_date", order)
        self.assertIn("refundable", order)

    def test_step_07_and_08_chatbot_worker_and_auditor_compliance(self):
        """Steps 7 & 8: SafeCart Chatbot Worker & Auditor Agents verification."""
        # 1. Product price query (Worker + Auditor)
        res_price = self.client.post("/api/chat", json={
            "query": "What is the price of Wireless Headphones?",
            "product_id": "P001"
        })
        self.assertEqual(res_price.status_code, 200)
        data_price = res_price.json()
        self.assertIn("1999", data_price.get("response", ""))
        self.assertEqual(data_price.get("audit", {}).get("audit_decision"), "APPROVED")

        # 2. Stock query
        res_stock = self.client.post("/api/chat", json={
            "query": "Is Bluetooth Speaker in stock?",
            "product_id": "P002"
        })
        self.assertEqual(res_stock.status_code, 200)
        data_stock = res_stock.json()
        self.assertIn("stock", data_stock.get("response", "").lower())
        self.assertEqual(data_stock.get("audit", {}).get("audit_decision"), "APPROVED")

        # 3. Order tracking query
        res_track = self.client.post("/api/chat", json={
            "query": "When will my order arrive?",
            "order_id": "O001"
        })
        self.assertEqual(res_track.status_code, 200)
        data_track = res_track.json()
        self.assertIn("2026-09-05", data_track.get("response", ""))
        self.assertEqual(data_track.get("audit", {}).get("audit_decision"), "APPROVED")

        # 4. Store policy compliance (Auditor catches out of stock hallucinations)
        worker_hallucination = {
            "status": "SUCCESS",
            "intent": "INVENTORY",
            "response": "Yes, P009 is in stock and available for immediate shipping with 50 units.",
            "database_verified": True
        }
        audit_hallucination = auditor_agent(
            query="Is P009 in stock?",
            order_id=None,
            product_id="P009",
            worker_result=worker_hallucination
        )
        self.assertEqual(audit_hallucination["audit_decision"], "CORRECTED")
        self.assertIn("out of stock", audit_hallucination["response"].lower())

    def test_step_09_and_10_demo_mode_and_design_preservation(self):
        """Steps 9 & 10: Verified ordering and Amazon clone design preservation without 'demo' labels."""
        html_path = PROJECT_ROOT / "amazon clone" / "Amazon.html"
        self.assertTrue(html_path.exists())
        content = html_path.read_text(encoding="utf-8")

        # Verified requirement: No "demo" labels displayed on website UI
        self.assertNotIn("DEMO MODE", content)
        self.assertNotIn("demo-top-bar", content)
        self.assertNotIn("Demo Mode Active", content)

        # Amazon layout preservation & modals
        self.assertIn("nav-logo", content)
        self.assertIn("shop-section", content)
        self.assertIn("foot-panel1", content)
        self.assertIn("safecart-chat-widget", content)
        self.assertIn("order-tracking-modal", content)

    def test_step_12_strict_category_filtering(self):
        """User requirement: Clicking a category shows ONLY that category, not all."""
        js_path = PROJECT_ROOT / "amazon clone" / "amazon_clone.js"
        self.assertTrue(js_path.exists())
        js_code = js_path.read_text(encoding="utf-8")

        self.assertIn("selectCategory", js_code)
        self.assertIn("categoryMatches", js_code)
        # Ensure category filtering logic isolates selected category
        self.assertIn("categoriesToRender = state.categories.filter", js_code)

    def test_step_11_image_matching_not_pid(self):
        """Specific constraint: Bluetooth Speaker displays Bluetooth Speaker image, not P101 badge."""
        js_path = PROJECT_ROOT / "amazon clone" / "amazon_clone.js"
        self.assertTrue(js_path.exists())
        js_code = js_path.read_text(encoding="utf-8")

        # Ensure PRODUCT_IMAGE_RULES contains bluetooth speaker
        self.assertIn("bluetooth speaker", js_code.lower())
        # Ensure card-id-badge was removed from product card HTML
        self.assertNotIn('<span class="card-id-badge">${pid}</span>', js_code)
        # Ensure handleProductImgError is defined
        self.assertIn("handleProductImgError", js_code)


if __name__ == "__main__":
    unittest.main()
