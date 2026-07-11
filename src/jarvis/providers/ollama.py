"""Ollama inference provider.

Wraps the local Ollama HTTP API for health checks, text generation, and
model listing. Configuration comes from `Settings` (`OLLAMA_HOST`,
`OLLAMA_MODEL`); connection failures are logged and surfaced as typed
exceptions rather than raw httpx errors.
"""

from functools import lru_cache
from typing import Any

import httpx

from jarvis.core.config import Settings, get_settings
from jarvis.core.logging import get_logger

logger = get_logger("jarvis.ollama")


class OllamaError(Exception):
    """Base exception for Ollama provider failures."""


class OllamaConnectionError(OllamaError):
    """Raised when the Ollama server cannot be reached."""


class OllamaResponseError(OllamaError):
    """Raised when Ollama returns an unexpected or error response."""


class OllamaClient:
    """HTTP client for the local Ollama inference API."""

    def __init__(
        self,
        settings: Settings,
        *,
        http_client: httpx.Client | None = None,
    ) -> None:
        self._settings = settings
        self._host = settings.ollama_host.rstrip("/")
        self._model = settings.ollama_model
        self._owns_client = http_client is None
        self._client = http_client or httpx.Client(
            base_url=self._host,
            timeout=httpx.Timeout(30.0),
        )

    @property
    def host(self) -> str:
        """Configured Ollama base URL."""
        return self._host

    @property
    def model(self) -> str:
        """Default model name used for generation."""
        return self._model

    def close(self) -> None:
        """Close the underlying HTTP client when owned by this instance."""
        if self._owns_client:
            self._client.close()

    def __enter__(self) -> "OllamaClient":
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def health_check(self) -> dict[str, Any]:
        """Check whether the Ollama server is reachable.

        Returns a dict with `healthy` (bool), `host`, and on failure an
        `error` message. Does not raise on connection errors.
        """
        try:
            response = self._client.get("/")
            response.raise_for_status()
            logger.debug("ollama_health_check_ok", host=self._host)
            return {"healthy": True, "host": self._host}
        except httpx.RequestError as exc:
            logger.warning(
                "ollama_health_check_failed",
                host=self._host,
                error=str(exc),
            )
            return {"healthy": False, "host": self._host, "error": str(exc)}
        except httpx.HTTPStatusError as exc:
            logger.warning(
                "ollama_health_check_failed",
                host=self._host,
                status_code=exc.response.status_code,
                error=str(exc),
            )
            return {
                "healthy": False,
                "host": self._host,
                "error": str(exc),
                "status_code": exc.response.status_code,
            }

    def generate(self, prompt: str) -> str:
        """Generate text from a prompt using the configured model.

        Args:
            prompt: The input prompt to send to Ollama.

        Returns:
            The generated response text.

        Raises:
            OllamaConnectionError: If the server cannot be reached.
            OllamaResponseError: If the response is missing or invalid.
        """
        payload = {
            "model": self._model,
            "prompt": prompt,
            "stream": False,
        }
        logger.info("ollama_generate_start", model=self._model, prompt_length=len(prompt))

        try:
            response = self._client.post("/api/generate", json=payload)
            response.raise_for_status()
        except httpx.RequestError as exc:
            logger.error(
                "ollama_generate_connection_error",
                host=self._host,
                model=self._model,
                error=str(exc),
            )
            raise OllamaConnectionError(
                f"Cannot connect to Ollama at {self._host}: {exc}"
            ) from exc
        except httpx.HTTPStatusError as exc:
            logger.error(
                "ollama_generate_http_error",
                host=self._host,
                model=self._model,
                status_code=exc.response.status_code,
                error=str(exc),
            )
            raise OllamaResponseError(
                f"Ollama returned HTTP {exc.response.status_code}: {exc}"
            ) from exc

        data = response.json()
        text = data.get("response")
        if not isinstance(text, str):
            logger.error(
                "ollama_generate_invalid_response",
                host=self._host,
                model=self._model,
                payload_keys=sorted(data.keys()) if isinstance(data, dict) else None,
            )
            raise OllamaResponseError("Ollama response missing 'response' field")

        logger.info(
            "ollama_generate_complete",
            model=self._model,
            response_length=len(text),
        )
        return text

    def list_models(self) -> list[str]:
        """Return names of models available on the Ollama server.

        Raises:
            OllamaConnectionError: If the server cannot be reached.
            OllamaResponseError: If the response is missing or invalid.
        """
        logger.debug("ollama_list_models_start", host=self._host)

        try:
            response = self._client.get("/api/tags")
            response.raise_for_status()
        except httpx.RequestError as exc:
            logger.error(
                "ollama_list_models_connection_error",
                host=self._host,
                error=str(exc),
            )
            raise OllamaConnectionError(
                f"Cannot connect to Ollama at {self._host}: {exc}"
            ) from exc
        except httpx.HTTPStatusError as exc:
            logger.error(
                "ollama_list_models_http_error",
                host=self._host,
                status_code=exc.response.status_code,
                error=str(exc),
            )
            raise OllamaResponseError(
                f"Ollama returned HTTP {exc.response.status_code}: {exc}"
            ) from exc

        data = response.json()
        models = data.get("models")
        if not isinstance(models, list):
            logger.error(
                "ollama_list_models_invalid_response",
                host=self._host,
                payload_keys=sorted(data.keys()) if isinstance(data, dict) else None,
            )
            raise OllamaResponseError("Ollama response missing 'models' field")

        names: list[str] = []
        for entry in models:
            if isinstance(entry, dict) and isinstance(entry.get("name"), str):
                names.append(entry["name"])

        logger.debug("ollama_list_models_complete", host=self._host, count=len(names))
        return names


@lru_cache(maxsize=1)
def get_ollama_client() -> OllamaClient:
    """Return a cached `OllamaClient` built from `get_settings()`.

    Use as a FastAPI dependency: `Depends(get_ollama_client)`.
    """
    return OllamaClient(get_settings())
