import urllib.request
import json
import sys

BASE_URL = "http://127.0.0.1:8000"

def test_live_api():
    print("=" * 70)
    print("      SafeCart Live HTTP API & Full Pipeline Verification Test")
    print("=" * 70)

    # 1. Health check
    try:
        req = urllib.request.Request(f"{BASE_URL}/health")
        with urllib.request.urlopen(req, timeout=5) as res:
            data = json.loads(res.read().decode())
            print(f"[PASS] Health check: {res.status} -> {data}")
            assert data.get("status") == "healthy"
    except Exception as e:
        print(f"[FAIL] Health check failed: {e}")
        return False

    test_queries = [
        {
            "num": "1",
            "desc": "Tell me about this product.",
            "payload": {"query": "Tell me about this product.", "product_id": "P001"},
            "expected_status": ["APPROVED", "CORRECTED"],
            "expected_content": "Wireless Headphones",
        },
        {
            "num": "2",
            "desc": "What is the price of this product?",
            "payload": {"query": "What is the price of this product?", "product_id": "P001"},
            "expected_status": ["APPROVED", "CORRECTED"],
            "expected_content": "1999",
        },
        {
            "num": "3",
            "desc": "Is this product available?",
            "payload": {"query": "Is this product available?", "product_id": "P001"},
            "expected_status": ["APPROVED", "CORRECTED"],
            "expected_content": "in stock",
        },
        {
            "num": "4",
            "desc": "Can I get a refund?",
            "payload": {"query": "Can I get a refund?", "order_id": "O001"},
            "expected_status": ["APPROVED", "CORRECTED"],
            "expected_content": "eligible for a refund",
        },
        {
            "num": "5",
            "desc": "When will my order arrive?",
            "payload": {"query": "When will my order arrive?", "order_id": "O001"},
            "expected_status": ["APPROVED", "CORRECTED"],
            "expected_content": "2026-09-05",
        },
        {
            "num": "6",
            "desc": "An invalid Product ID.",
            "payload": {"query": "What is the price of this item?", "product_id": "P_INVALID_999"},
            "expected_status": ["ERROR"],
            "expected_content": "valid Product ID",
        },
        {
            "num": "7",
            "desc": "An invalid Order ID.",
            "payload": {"query": "When will my order arrive?", "order_id": "O_INVALID_999"},
            "expected_status": ["ERROR"],
            "expected_content": "valid Order ID",
        },
        {
            "num": "8",
            "desc": "An unclear customer question.",
            "payload": {"query": "Hello, can you help me with information?"},
            "expected_status": ["APPROVED"],
            "expected_content": "help you with",
        }
    ]

    failed = 0
    for item in test_queries:
        try:
            req = urllib.request.Request(
                f"{BASE_URL}/api/chat",
                data=json.dumps(item["payload"]).encode("utf-8"),
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=5) as res:
                data = json.loads(res.read().decode())
                status = data.get("status")
                response_text = data.get("response", "")
                
                status_ok = status in item["expected_status"]
                content_ok = item["expected_content"].lower() in response_text.lower()
                
                if status_ok and content_ok:
                    print(f"[PASS] Test {item['num']}: '{item['desc']}'")
                    print(f"       Outcome: status={status} | response={response_text[:80]}...")
                else:
                    print(f"[FAIL] Test {item['num']}: '{item['desc']}'")
                    print(f"       Got: status={status}, response={response_text}")
                    failed += 1
        except Exception as e:
            print(f"[FAIL] Test {item['num']}: '{item['desc']}' encountered exception: {e}")
            failed += 1

    print("-" * 70)
    if failed == 0:
        print("[PASS] ALL 8 REAL CUSTOMER QUERY TESTS PASSED VIA HTTP API!")
        print("=" * 70)
        return True
    else:
        print(f"[FAIL] {failed} live queries failed.")
        print("=" * 70)
        return False

if __name__ == "__main__":
    success = test_live_api()
    sys.exit(0 if success else 1)
