import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from auditor_agent import auditor_agent
from worker_agent import worker_agent

def test_auditor():
    print("=" * 60)
    print("           SafeCart Auditor Agent Test Suite")
    print("=" * 60)

    test_cases = [
        # CASE 1: Worker gives correct price
        {
            "name": "CASE 1: Worker gives a correct price",
            "query": "What is the price of this product?",
            "product_id": "P001",
            "order_id": None,
            "worker_result": {
                "status": "SUCCESS",
                "intent": "PRICE",
                "response": "The price of Wireless Headphones is Rs. 1999.",
                "database_verified": True
            },
            "expected_decision": "APPROVED",
            "expected_status": "APPROVED",
            "validate": lambda r: "1999" in r["response"] and r["audit_decision"] == "APPROVED"
        },
        # CASE 2: Worker gives incorrect price
        {
            "name": "CASE 2: Worker gives an incorrect price (invented Rs. 999 instead of 1999)",
            "query": "What is the price of this product?",
            "product_id": "P001",
            "order_id": None,
            "worker_result": {
                "status": "SUCCESS",
                "intent": "PRICE",
                "response": "The price of Wireless Headphones is Rs. 999.",
                "database_verified": True
            },
            "expected_decision": "CORRECTED",
            "expected_status": "CORRECTED",
            "validate": lambda r: "1999" in r["response"] and r["audit_decision"] == "CORRECTED" and len(r["errors"]) > 0
        },
        # CASE 3: Worker says in stock but inventory says quantity = 0 (P009)
        {
            "name": "CASE 3: Worker claims product is in stock when quantity is 0",
            "query": "Is this product in stock?",
            "product_id": "P009",
            "order_id": None,
            "worker_result": {
                "status": "SUCCESS",
                "intent": "INVENTORY",
                "response": "The product is currently in stock. Available quantity: 50.",
                "database_verified": True
            },
            "expected_decision": "CORRECTED",
            "expected_status": "CORRECTED",
            "validate": lambda r: "out of stock" in r["response"].lower() and r["audit_decision"] == "CORRECTED"
        },
        # CASE 4: Worker says order is refundable but database says it is not (O010)
        {
            "name": "CASE 4: Worker claims order is refundable when DB says not refundable",
            "query": "Can I get a refund for my order?",
            "product_id": None,
            "order_id": "O010",
            "worker_result": {
                "status": "SUCCESS",
                "intent": "REFUND",
                "response": "Order O010 is eligible for a refund according to the policy.",
                "database_verified": True
            },
            "expected_decision": "CORRECTED",
            "expected_status": "CORRECTED",
            "validate": lambda r: "not eligible for a refund" in r["response"] and r["audit_decision"] == "CORRECTED"
        },
        # CASE 5: Delivery date does not exist / invalid order ID
        {
            "name": "CASE 5: Delivery date requested for non-existent order (must not invent date)",
            "query": "When will my order arrive?",
            "product_id": None,
            "order_id": "O9999",
            "worker_result": {
                "status": "ERROR",
                "intent": "DELIVERY",
                "response": "Please provide a valid Order ID.",
                "database_verified": False
            },
            "expected_decision": "REJECTED",
            "expected_status": "ERROR",
            "validate": lambda r: "valid Order ID" in r["response"] and r["audit_decision"] == "REJECTED"
        },
        # CASE 6: Product ID does not exist (must not invent info)
        {
            "name": "CASE 6: Product ID does not exist",
            "query": "What is the price of this product?",
            "product_id": "P999999",
            "order_id": None,
            "worker_result": {
                "status": "ERROR",
                "intent": "PRICE",
                "response": "Please provide a valid Product ID.",
                "database_verified": False
            },
            "expected_decision": "REJECTED",
            "expected_status": "ERROR",
            "validate": lambda r: "valid Product ID" in r["response"] and r["audit_decision"] == "REJECTED"
        },
        # CASE 7: Order ID does not exist (must not invent order info)
        {
            "name": "CASE 7: Order ID does not exist",
            "query": "Can I get a refund?",
            "product_id": None,
            "order_id": "O999999",
            "worker_result": {
                "status": "ERROR",
                "intent": "REFUND",
                "response": "Please provide a valid Order ID.",
                "database_verified": False
            },
            "expected_decision": "REJECTED",
            "expected_status": "ERROR",
            "validate": lambda r: "valid Order ID" in r["response"] and r["audit_decision"] == "REJECTED"
        }
    ]

    failed = 0
    for tc in test_cases:
        res = auditor_agent(
            query=tc["query"],
            order_id=tc["order_id"],
            product_id=tc["product_id"],
            worker_result=tc["worker_result"]
        )
        passed = (
            res.get("audit_decision") == tc["expected_decision"]
            and res.get("status") == tc["expected_status"]
            and tc["validate"](res)
        )
        status_str = "PASS" if passed else "FAIL"
        if not passed:
            failed += 1

        print(f"[{status_str}] {tc['name']}")
        print(f"       Decision: {res.get('audit_decision')} | Status: {res.get('status')}")
        print(f"       Response: {res.get('response')}")
        if res.get("errors"):
            print(f"       Audit Errors: {res.get('errors')}")
        if res.get("corrections"):
            print(f"       Corrections: {res.get('corrections')}")

    print("-" * 60)
    if failed == 0:
        print("[PASS] ALL AUDITOR TEST CASES (CASES 1-7) PASSED!")
        print("=" * 60)
        return True
    else:
        print(f"[FAIL] {failed} Auditor test cases failed.")
        print("=" * 60)
        return False

if __name__ == "__main__":
    success = test_auditor()
    sys.exit(0 if success else 1)
