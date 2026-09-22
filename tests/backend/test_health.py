import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "apps" / "api"))

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_root_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_v1_health() -> None:
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
