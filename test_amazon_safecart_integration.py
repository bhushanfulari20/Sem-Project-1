"""
SafeCart Amazon Clone Integration Verification Test Suite
Tests:
1. Product Loading (All 500 products from Database/products.csv without duplicate or fake items)
2. Live Prices & Stock Availability reflection from Database/inventory.csv
3. Product Search and Category Filtering
4. Cart Validation API
5. Order Placement & Inventory Decrement in SafeCart Database
6. Order Retrieval & Tracking from Database/orders.csv
7. SafeCart AI Chatbot Worker + Auditor Agents Verification
8. Amazon Clone Static Files and Routes
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


class TestSafeCartAmazonIntegration(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_01_all_500_products_loaded(self):
        """Requirement 1 & 2: Display all 500 existing products from SafeCart database."""
        res = self.client.get("/api/products?limit=500")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data.get("status"), "SUCCESS")
        self.assertEqual(data.get("total"), 500)
        self.assertEqual(len(data.get("products")), 500)
        
        # Verify first product
        p001 = data["products"][0]
        self.assertEqual(p001["product_id"], "P001")
        self.assertEqual(p001["product_name"], "Wireless Headphones")
        self.assertEqual(p001["category"], "Electronics")
        self.assertEqual(p001["price"], 1999)
        self.assertIn("quantity", p001)
        self.assertIn("in_stock", p001)

    def test_02_single_product_and_live_inventory(self):
        """Requirement 3 & 4: Ensure product prices and stock availability reflect actual database."""
        # P001 has 25 stock
        res = self.client.get("/api/products/P001")
        self.assertEqual(res.status_code, 200)
        p001 = res.json().get("product")
        self.assertEqual(p001["product_id"], "P001")
        self.assertEqual(p001["price"], 1999)
        
        # P009 is out of stock (0 quantity) in inventory.csv
        res9 = self.client.get("/api/products/P009")
        self.assertEqual(res9.status_code, 200)
        p009 = res9.json().get("product")
        self.assertEqual(p009["product_id"], "P009")
        self.assertEqual(p009["quantity"], 0)
        self.assertFalse(p009["in_stock"])

    def test_03_categories_retrieval(self):
        """Categories API reflects SafeCart database unique categories."""
        res = self.client.get("/api/categories")
        self.assertEqual(res.status_code, 200)
        cats = res.json().get("categories", [])
        self.assertGreaterEqual(len(cats), 15)
        self.assertIn("Electronics", cats)
        self.assertIn("Clothing", cats)
        self.assertIn("Mobiles", cats)
        self.assertIn("Personal Care", cats)

    def test_04_product_search_and_category_filter(self):
        """Search and category filtering against SafeCart database."""
        # Search query
        res = self.client.get("/api/products?search=headphones")
        self.assertEqual(res.status_code, 200)
        products = res.json().get("products", [])
        self.assertTrue(any("headphone" in p["product_name"].lower() for p in products))

        # Category filter
        res_cat = self.client.get("/api/products?category=Electronics&limit=500")
        self.assertEqual(res_cat.status_code, 200)
        elec_products = res_cat.json().get("products", [])
        self.assertGreater(len(elec_products), 0)
        self.assertTrue(all(p["category"] == "Electronics" for p in elec_products))

    def test_05_cart_validation(self):
        """Cart validation against live database prices and stock."""
        items = [
            {"product_id": "P001", "quantity": 2},
            {"product_id": "P002", "quantity": 1}
        ]
        res = self.client.post("/api/cart/validate", json=items)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data.get("status"), "SUCCESS")
        self.assertEqual(len(data.get("items")), 2)
        # P001 price is 1999 * 2 = 3998, P002 price is 1499 * 1 = 1499, subtotal = 5497
        expected_subtotal = (1999 * 2) + (1499 * 1)
        self.assertEqual(data.get("subtotal"), expected_subtotal)
        self.assertTrue(data.get("all_available"))

    def test_06_order_placement_and_inventory_decrement(self):
        """Requirement 5: Save order in existing SafeCart database and update inventory safely."""
        # Choose product P050 and check current stock (replenish if depleted from earlier test runs)
        prod_before = db.get_product_with_inventory("P050")
        if prod_before["quantity"] <= 1:
            db.update_inventory("P050", 25)
            prod_before = db.get_product_with_inventory("P050")
        qty_before = prod_before["quantity"]
        self.assertGreater(qty_before, 0)

        # Place single order via API
        payload = {
            "product_id": "P050",
            "quantity": 1,
            "customer_name": "Test Integration Customer",
            "customer_email": "test@amazon.in",
            "shipping_address": "Test Street, Mumbai, India"
        }
        res = self.client.post("/api/orders", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data.get("status"), "SUCCESS")
        order = data.get("order")
        self.assertIsNotNone(order)
        new_order_id = order.get("order_id")
        self.assertTrue(new_order_id.startswith("O"))

        # Verify stock decremented by 1 in database
        prod_after = db.get_product_with_inventory("P050")
        self.assertEqual(prod_after["quantity"], qty_before - 1)

        # Verify order exists in SafeCart database
        saved_order = db.find_order(new_order_id)
        self.assertIsNotNone(saved_order)
        self.assertEqual(saved_order["product_id"], "P050")

    def test_07_checkout_cart_multiple_items(self):
        """Checkout cart with multiple items updates SafeCart database correctly."""
        # Check stock for P051 and P052 (replenish if depleted from earlier test runs)
        p51_before = db.get_product_with_inventory("P051")
        p52_before = db.get_product_with_inventory("P052")
        if p51_before["quantity"] <= 1:
            db.update_inventory("P051", 25)
            p51_before = db.get_product_with_inventory("P051")
        if p52_before["quantity"] <= 1:
            db.update_inventory("P052", 25)
            p52_before = db.get_product_with_inventory("P052")
        self.assertGreater(p51_before["quantity"], 0)
        self.assertGreater(p52_before["quantity"], 0)

        payload = {
            "items": [
                {"product_id": "P051", "quantity": 1},
                {"product_id": "P052", "quantity": 1}
            ],
            "customer_name": "Multi Item Shopper",
            "customer_email": "shopper@amazon.in",
            "shipping_address": "Pune, India"
        }
        res = self.client.post("/api/checkout", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data.get("status"), "SUCCESS")
        self.assertEqual(len(data.get("orders")), 2)

        # Verify stock decremented
        p51_after = db.get_product_with_inventory("P051")
        p52_after = db.get_product_with_inventory("P052")
        self.assertEqual(p51_after["quantity"], p51_before["quantity"] - 1)
        self.assertEqual(p52_after["quantity"], p52_before["quantity"] - 1)

    def test_08_chatbot_worker_auditor_compliance(self):
        """Requirement 6 & 7: SafeCart chatbot integrates Worker + Auditor AI."""
        # 1. Price query
        res_price = self.client.post("/api/chat", json={
            "query": "What is the price of Wireless Headphones?",
            "product_id": "P001"
        })
        self.assertEqual(res_price.status_code, 200)
        data_price = res_price.json()
        self.assertIn(data_price.get("status"), ["APPROVED", "CORRECTED"])
        self.assertIn("1999", data_price.get("response"))
        self.assertIn("audit", data_price)

        # 2. Stock query
        res_stock = self.client.post("/api/chat", json={
            "query": "Is this product available in stock?",
            "product_id": "P001"
        })
        self.assertEqual(res_stock.status_code, 200)
        data_stock = res_stock.json()
        self.assertIn(data_stock.get("status"), ["APPROVED", "CORRECTED"])
        self.assertIn("in stock", data_stock.get("response").lower())

        # 3. Out of stock query (P009 has 0 stock)
        res_oos = self.client.post("/api/chat", json={
            "query": "Is this product available in stock?",
            "product_id": "P009"
        })
        self.assertEqual(res_oos.status_code, 200)
        data_oos = res_oos.json()
        self.assertIn("out of stock", data_oos.get("response").lower())

        # 4. Delivery tracking query
        res_track = self.client.post("/api/chat", json={
            "query": "When will my order arrive?",
            "order_id": "O001"
        })
        self.assertEqual(res_track.status_code, 200)
        data_track = res_track.json()
        self.assertIn("2026-09-05", data_track.get("response"))

        # 5. Refund policy query
        res_refund = self.client.post("/api/chat", json={
            "query": "Can I get a refund for this order?",
            "order_id": "O001"
        })
        self.assertEqual(res_refund.status_code, 200)
        data_refund = res_refund.json()
        self.assertIn("eligible for a refund", data_refund.get("response").lower())

    def test_09_amazon_clone_routes(self):
        """Requirement 8: Amazon clone UI served and assets accessible."""
        # /amazon route
        res = self.client.get("/amazon")
        self.assertEqual(res.status_code, 200)
        self.assertIn("text/html", res.headers.get("content-type", ""))
        self.assertIn("Amazon Clone", res.text)
        self.assertIn("SafeCart", res.text)
        self.assertIn("catalog-section", res.text)

        # /amazon/amazon_clone.js
        res_js = self.client.get("/amazon/amazon_clone.js")
        self.assertEqual(res_js.status_code, 200)
        self.assertIn("SafeCart Amazon Clone", res_js.text)

        # /amazon/style.css
        res_css = self.client.get("/amazon/style.css")
        self.assertEqual(res_css.status_code, 200)
        self.assertIn("catalog-section", res_css.text)

    def test_10_database_synchronization_stock_update(self):
        """Requirement 8: Synchronize stock changes with SafeCart database."""
        # 1. Fetch current stock for P003
        inv_before = db.get_inventory("P003")
        qty_before = int(inv_before["quantity"])

        try:
            # 2. Update stock via API
            new_qty = 42
            res = self.client.patch("/api/products/P003/stock", json={"quantity": new_qty})
            self.assertEqual(res.status_code, 200)
            data = res.json()
            self.assertEqual(data.get("status"), "SUCCESS")
            self.assertEqual(data["inventory"]["quantity"], new_qty)

            # 3. Verify single source of truth in database
            inv_db = db.get_inventory("P003")
            self.assertEqual(int(inv_db["quantity"]), new_qty)
            
            # 4. Verify product endpoint reflects updated stock
            res_prod = self.client.get("/api/products/P003")
            self.assertEqual(res_prod.status_code, 200)
            self.assertEqual(res_prod.json()["product"]["quantity"], new_qty)
        finally:
            # 5. Restore original stock
            db.set_inventory("P003", qty_before)
            self.assertEqual(int(db.get_inventory("P003")["quantity"]), qty_before)

    def test_11_database_synchronization_add_and_delete_product(self):
        """Requirement 8: Synchronize product additions and deletions with SafeCart database."""
        payload = {
            "product_name": "Ultra Soundbar 5.1",
            "category": "Electronics",
            "price": 7999,
            "description": "High fidelity surround sound home theatre bar",
            "initial_stock": 18
        }
        res = self.client.post("/api/products", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data.get("status"), "SUCCESS")
        new_prod = data.get("product")
        new_pid = new_prod.get("product_id")
        self.assertTrue(new_pid.startswith("P"))
        self.assertEqual(new_prod["quantity"], 18)

        try:
            # Verify single source of truth in database
            fetched = db.find_product(new_pid)
            self.assertIsNotNone(fetched)
            self.assertEqual(fetched["product_name"], "Ultra Soundbar 5.1")
            inv_row = db.get_inventory(new_pid)
            self.assertEqual(int(inv_row["quantity"]), 18)
        finally:
            # Clean up added product to preserve 500 baseline items for test_database.py
            del_res = self.client.delete(f"/api/products/{new_pid}")
            self.assertEqual(del_res.status_code, 200)
            self.assertIsNone(db.find_product(new_pid))
            self.assertIsNone(db.get_inventory(new_pid))
            
            # Verify database is back to exactly 500 products
            all_prods = db.load_csv(db.PRODUCTS_FILE)
            self.assertEqual(len(all_prods), 500)

    def test_12_category_wise_display_and_unique_images(self):
        """Requirement 1, 2, 3: Category-wise structure, unique product attributes, and template UI elements."""
        # 1. Fetch categories
        res_cats = self.client.get("/api/categories")
        self.assertEqual(res_cats.status_code, 200)
        categories = res_cats.json().get("categories", [])
        self.assertGreaterEqual(len(categories), 15)

        # 2. Fetch all products and verify distribution
        res_prods = self.client.get("/api/products?limit=500")
        self.assertEqual(res_prods.status_code, 200)
        products = res_prods.json().get("products", [])
        self.assertEqual(len(products), 500)

        # Verify every product has valid category, positive price, and valid stock
        seen_pids = set()
        for p in products:
            self.assertIn(p["category"], categories)
            self.assertGreater(p["price"], 0)
            self.assertGreaterEqual(p["quantity"], 0)
            self.assertTrue(len(p["product_name"]) > 0)
            seen_pids.add(p["product_id"])
        self.assertEqual(len(seen_pids), 500)

        # 3. Verify HTML template contains category-shelves and view-mode toggles
        res_html = self.client.get("/amazon")
        self.assertEqual(res_html.status_code, 200)
        self.assertIn("category-shelves-container", res_html.text)
        self.assertIn("view-mode-shelves-btn", res_html.text)
        self.assertIn("view-mode-grid-btn", res_html.text)
        self.assertIn("db-sync-modal", res_html.text)


if __name__ == "__main__":
    unittest.main()
