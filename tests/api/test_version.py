from fastapi.testclient import TestClient

from jarvis import __version__


def test_version_returns_200(client: TestClient) -> None:
    response = client.get("/api/v1/version")
    assert response.status_code == 200


def test_version_response_shape(client: TestClient) -> None:
    response = client.get("/api/v1/version")
    body = response.json()

    assert body["version"] == __version__
    assert body["app_name"] == "Jarvis"
    assert body["environment"] == "development"
