import sys
from pathlib import Path

# Add Backend and project root to sys.path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from rules import (
    get_rules,
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

def test_rules():
    print("=" * 60)
    print("             SafeCart Rules.py Test Suite")
    print("=" * 60)

    rules = get_rules()
    print(f"Safety rules loaded: {len(rules)}")
    assert len(rules) >= 7, f"Expected at least 7 safety rules, got {len(rules)}"

    test_cases = [
        # (query, expected_predicate_name, predicate_fn)
        ("What is the price of this product?", "PRICE", is_price_query),
        ("How much does this cost?", "PRICE", is_price_query),
        ("Is this product available?", "INVENTORY", is_inventory_query),
        ("How many items are in stock?", "INVENTORY", is_inventory_query),
        ("Can I get a refund?", "REFUND", is_refund_query),
        ("I want my money back", "REFUND", is_refund_query),
        ("When will my order arrive?", "DELIVERY", is_delivery_query),
        ("What is the delivery date?", "DELIVERY", is_delivery_query),
        ("Tell me about this product.", "PRODUCT_INFO", is_product_info_query),
        ("What are the features and specifications?", "PRODUCT_INFO", is_product_info_query),
        ("What is your refund policy?", "POLICY", is_policy_query),
        ("Where is my order? Track order", "ORDER_STATUS", is_order_status_query),
        ("I want to cancel my order", "CANCELLATION", is_cancellation_query),
        ("The product is damaged upon arrival", "COMPLAINT", is_complaint_query),
        ("Can I return this item?", "RETURN", is_return_query),
    ]

    failed = 0
    for query, intent, fn in test_cases:
        matched = fn(query)
        status = "PASS" if matched else "FAIL"
        if not matched:
            failed += 1
        print(f"[{status}] Query: '{query}' -> Expected Intent: {intent} (Matched: {matched})")

    print("-" * 60)
    if failed == 0:
        print("[PASS] ALL RULES TESTS PASSED!")
        print("=" * 60)
        return True
    else:
        print(f"[FAIL] {failed} rules tests failed.")
        print("=" * 60)
        return False

if __name__ == "__main__":
    success = test_rules()
    sys.exit(0 if success else 1)
