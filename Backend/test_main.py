import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from fastapi.testclient import TestClient
from main import app

def test_api():
    print("=" * 60)
    print("            SafeCart FastAPI Backend Test Suite")
    print("=" * 60)

    client = TestClient(app)

    # 1. Health check
    res = client.get("/health")
    print(f"GET /health: {res.status_code} -> {res.json()}")
    assert res.status_code == 200
    assert res.json().get("status") == "healthy"

    # 2. Root check
    res = client.get("/")
    print(f"GET /: {res.status_code}")
    assert res.status_code == 200

    # 3. Chat endpoint with empty query
    res = client.post("/api/chat", json={"query": ""})
    print(f"POST /api/chat (empty query): {res.status_code} -> {res.json()}")
    assert res.status_code == 200
    assert res.json().get("status") == "ERROR"

    # 4. Chat endpoint with valid price query
    res = client.post("/api/chat", json={
        "query": "What is the price of this product?",
        "product_id": "P001"
    })
    print(f"POST /api/chat (price query): {res.status_code} -> {res.json().get('status')} | {res.json().get('response')}")
    assert res.status_code == 200
    assert res.json().get("status") in ["APPROVED", "CORRECTED"]
    assert "1999" in res.json().get("response")

    # 5. Chat endpoint with refund query
    res = client.post("/api/chat", json={
        "query": "Can I get a refund?",
        "order_id": "O001"
    })
    print(f"POST /api/chat (refund query): {res.status_code} -> {res.json().get('status')} | {res.json().get('response')}")
    assert res.status_code == 200
    assert res.json().get("status") in ["APPROVED", "CORRECTED"]

    # 6. Chat endpoint with invalid ID
    res = client.post("/api/chat", json={
        "query": "When will my order arrive?",
        "order_id": "O_INVALID_999"
    })
    print(f"POST /api/chat (invalid order): {res.status_code} -> {res.json().get('status')} | {res.json().get('response')}")
    assert res.status_code == 200
    assert res.json().get("status") == "ERROR"

    print("-" * 60)
    print("[PASS] ALL FASTAPI BACKEND TESTS PASSED!")
    print("=" * 60)
    return True

if __name__ == "__main__":
    success = test_api()
    sys.exit(0 if success else 1)
