import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from worker_agent import worker_agent

def test_worker():
    print("=" * 60)
    print("           SafeCart Worker Agent Comprehensive Tests")
    print("=" * 60)

    test_cases = [
        {
            "name": "1. Product information query",
            "query": "Tell me about this product.",
            "product_id": "P001",
            "order_id": None,
            "expected_intent": "PRODUCT_INFO",
            "expected_status": "SUCCESS",
            "check": lambda res: "Wireless Headphones" in res["response"] and res["database_verified"]
        },
        {
            "name": "2. Price query",
            "query": "What is the price of this product?",
            "product_id": "P001",
            "order_id": None,
            "expected_intent": "PRICE",
            "expected_status": "SUCCESS",
            "check": lambda res: "1999" in res["response"] and res["database_verified"]
        },
        {
            "name": "3. Inventory query",
            "query": "Is this product available in stock?",
            "product_id": "P001",
            "order_id": None,
            "expected_intent": "INVENTORY",
            "expected_status": "SUCCESS",
            "check": lambda res: "in stock" in res["response"] and "25" in res["response"] and res["database_verified"]
        },
        {
            "name": "4. Refund query",
            "query": "Can I get a refund for my order?",
            "product_id": None,
            "order_id": "O001",
            "expected_intent": "REFUND",
            "expected_status": "SUCCESS",
            "check": lambda res: "eligible for a refund" in res["response"] and res["database_verified"]
        },
        {
            "name": "5. Delivery query",
            "query": "When will my order arrive?",
            "product_id": None,
            "order_id": "O001",
            "expected_intent": "DELIVERY",
            "expected_status": "SUCCESS",
            "check": lambda res: "2026-09-05" in res["response"] and res["database_verified"]
        },
        {
            "name": "6. General query",
            "query": "Hello, how can you help me today?",
            "product_id": None,
            "order_id": None,
            "expected_intent": "GENERAL",
            "expected_status": "SUCCESS",
            "check": lambda res: "help you with" in res["response"] and not res["database_verified"]
        },
        {
            "name": "7. Invalid Product ID",
            "query": "What is the price of this item?",
            "product_id": "P999999",
            "order_id": None,
            "expected_intent": "PRICE",
            "expected_status": "ERROR",
            "check": lambda res: not res["database_verified"] and "valid Product ID" in res["response"]
        },
        {
            "name": "8. Invalid Order ID",
            "query": "When will my order arrive?",
            "product_id": None,
            "order_id": "O999999",
            "expected_intent": "DELIVERY",
            "expected_status": "ERROR",
            "check": lambda res: not res["database_verified"] and "valid Order ID" in res["response"]
        },
        {
            "name": "9. Missing Product ID",
            "query": "Tell me about this product.",
            "product_id": None,
            "order_id": None,
            "expected_intent": "PRODUCT_INFO",
            "expected_status": "ERROR",
            "check": lambda res: not res["database_verified"] and "valid Product ID" in res["response"]
        },
        {
            "name": "10. Missing Order ID",
            "query": "Can I get a refund?",
            "product_id": None,
            "order_id": None,
            "expected_intent": "REFUND",
            "expected_status": "ERROR",
            "check": lambda res: not res["database_verified"] and "valid Order ID" in res["response"]
        },
        {
            "name": "11. Unclear question",
            "query": "asdf qwerty 12345 ???",
            "product_id": None,
            "order_id": None,
            "expected_intent": "GENERAL",
            "expected_status": "SUCCESS",
            "check": lambda res: "help you with" in res["response"]
        }
    ]

    failed = 0
    for tc in test_cases:
        res = worker_agent(query=tc["query"], order_id=tc["order_id"], product_id=tc["product_id"])
        intent_ok = res.get("intent") == tc["expected_intent"]
        status_ok = res.get("status") == tc["expected_status"]
        check_ok = tc["check"](res)
        passed = intent_ok and status_ok and check_ok

        status_str = "PASS" if passed else "FAIL"
        if not passed:
            failed += 1
        print(f"[{status_str}] {tc['name']}")
        print(f"       Intent: {res.get('intent')} | Status: {res.get('status')} | Verified: {res.get('database_verified')}")
        print(f"       Response: {res.get('response')}")

    print("-" * 60)
    if failed == 0:
        print("[PASS] ALL 11 WORKER AGENT TESTS PASSED!")
        print("=" * 60)
        return True
    else:
        print(f"[FAIL] {failed} Worker tests failed.")
        print("=" * 60)
        return False

if __name__ == "__main__":
    success = test_worker()
    sys.exit(0 if success else 1)
