from fastapi.testclient import TestClient

from app.main import app


def test_login_and_health():
    with TestClient(app) as client:
        assert client.get("/health").status_code == 200
        res = client.post("/auth/login", json={"username": "doctor", "password": "doctor123"})
        assert res.status_code == 200
        assert res.json()["user"]["role"] == "医生"


def test_bad_login_rejected():
    with TestClient(app) as client:
        res = client.post("/auth/login", json={"username": "doctor", "password": "bad"})
        assert res.status_code == 401
