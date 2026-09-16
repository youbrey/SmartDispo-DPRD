from fastapi.testclient import TestClient

from app.main import app


def test_health() -> None:
    response = TestClient(app).get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert response.headers["X-RateLimit-Limit"]
    assert response.headers["X-Content-Type-Options"] == "nosniff"
