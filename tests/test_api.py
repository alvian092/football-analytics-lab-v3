from fastapi.testclient import TestClient
from backend.app.main import app
client = TestClient(app)

def test_health():
    assert client.get("/api/health").status_code == 200

def test_upload_rejects_bad_schema():
    response = client.post("/api/data/csv", files={"file": ("bad.csv", b"hello\nworld", "text/csv")})
    assert response.status_code == 400

def test_analyze_requires_data():
    response = client.post("/api/analyze", json={"home_team":"A","away_team":"B","as_of":"2026-01-01"})
    assert response.status_code in (409, 422)
