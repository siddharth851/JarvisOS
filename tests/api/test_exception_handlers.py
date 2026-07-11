from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from pydantic import BaseModel

from jarvis.api.exceptions import register_exception_handlers
from jarvis.api.middleware import RequestIDMiddleware


class _Widget(BaseModel):
    name: str
    quantity: int


def _build_faulty_app() -> FastAPI:
    """A minimal app with routes that deliberately raise, to exercise
    the global exception handlers in isolation from the real app.
    """
    app = FastAPI()
    app.add_middleware(RequestIDMiddleware)
    register_exception_handlers(app)

    @app.get("/boom")
    async def boom() -> None:
        raise ValueError("something broke")

    @app.get("/not-found")
    async def not_found() -> None:
        raise HTTPException(status_code=404, detail="widget not found")

    @app.post("/widgets")
    async def create_widget(widget: _Widget) -> _Widget:
        return widget

    return app


def test_unhandled_exception_returns_500_json() -> None:
    client = TestClient(_build_faulty_app(), raise_server_exceptions=False)
    response = client.get("/boom")

    assert response.status_code == 500
    assert response.json() == {"error": "Internal server error"}


def test_http_exception_returns_matching_status_and_detail() -> None:
    client = TestClient(_build_faulty_app())
    response = client.get("/not-found")

    assert response.status_code == 404
    assert response.json() == {"error": "widget not found"}


def test_validation_error_returns_422() -> None:
    client = TestClient(_build_faulty_app())
    response = client.post("/widgets", json={"name": "bolt"})  # missing "quantity"

    assert response.status_code == 422
    body = response.json()
    assert body["error"] == "Validation failed"
    assert any(err["loc"][-1] == "quantity" for err in body["detail"])


def test_health_endpoint_unaffected_by_exception_handlers(client: TestClient) -> None:
    response = client.get("/api/v1/health")
    assert response.status_code == 200
