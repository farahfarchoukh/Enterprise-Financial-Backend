from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

def test_health():
    res = client.get("/health")
    assert res.status_code == 200

def test_unauth_access():
    res = client.post("/api/v1/analyze", json={"question": "hi"})
    assert res.status_code == 403 # Missing Admin Key