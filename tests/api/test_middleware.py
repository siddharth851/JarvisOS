import uuid

from fastapi.testclient import TestClient


def test_generates_request_id_when_absent(client: TestClient) -> None:
    response = client.get("/api/v1/health")
    request_id = response.headers["X-Request-ID"]
    # Should be a valid UUID4 when the client didn't supply one
    assert uuid.UUID(request_id).version == 4


def test_reuses_inbound_request_id(client: TestClient) -> None:
    inbound_id = "test-correlation-id-123"
    response = client.get("/api/v1/health", headers={"X-Request-ID": inbound_id})
    assert response.headers["X-Request-ID"] == inbound_id


def test_each_request_gets_a_distinct_id(client: TestClient) -> None:
    first = client.get("/api/v1/health").headers["X-Request-ID"]
    second = client.get("/api/v1/health").headers["X-Request-ID"]
    assert first != second


def test_request_logging_emits_structured_log(
    client: TestClient, caplog: "object"
) -> None:
    import logging as std_logging

    with caplog.at_level(std_logging.INFO, logger="jarvis.request"):  # type: ignore[attr-defined]
        client.get("/api/v1/health")

    matching = [
        r
        for r in caplog.records  # type: ignore[attr-defined]
        if r.name == "jarvis.request" and isinstance(r.msg, dict) and r.msg.get("event") == "http_request"
    ]
    assert len(matching) == 1
    event_dict = matching[0].msg
    assert event_dict["path"] == "/api/v1/health"
    assert event_dict["status_code"] == 200
    assert event_dict["method"] == "GET"


def test_cors_headers_present_on_preflight(client: TestClient) -> None:
    response = client.options(
        "/api/v1/health",
        headers={
            "Origin": "http://example.com",
            "Access-Control-Request-Method": "GET",
        },
    )
    # With allow_credentials=True, the CORS spec forbids a literal "*"
    # allow-origin response; Starlette correctly echoes the request's
    # origin instead so credentialed cross-origin requests still work.
    assert response.headers.get("access-control-allow-origin") == "http://example.com"
    assert response.headers.get("access-control-allow-credentials") == "true"
