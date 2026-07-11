from datetime import datetime

from fastapi.testclient import TestClient

from jarvis import __version__


def test_health_returns_200(client: TestClient) -> None:
    response = client.get("/api/v1/health")
    assert response.status_code == 200


def test_health_response_shape(client: TestClient) -> None:
    response = client.get("/api/v1/health")
    body = response.json()

    assert body["status"] == "healthy"
    assert body["version"] == __version__
    assert body["environment"] == "development"
    # Must be a valid ISO-8601 timestamp
    datetime.fromisoformat(body["timestamp"])


def test_health_includes_request_id_header(client: TestClient) -> None:
    response = client.get("/api/v1/health")
    assert "X-Request-ID" in response.headers
