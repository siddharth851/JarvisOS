"""Chat service.

Orchestrates user messages through the Ollama provider. Keeps HTTP concerns
in the API layer; this module owns chat business logic only.
"""

from dataclasses import dataclass
from datetime import UTC, datetime
from functools import lru_cache

from jarvis.core.logging import get_logger
from jarvis.providers.ollama import OllamaClient, get_ollama_client

logger = get_logger("jarvis.chat")


@dataclass(frozen=True)
class ChatResult:
    """Result of a single chat turn."""

    response: str
    model: str
    timestamp: datetime


class ChatService:
    """Handles chat message processing via Ollama."""

    def __init__(self, ollama_client: OllamaClient) -> None:
        self._ollama = ollama_client

    def chat(self, message: str) -> ChatResult:
        """Send a user message to Ollama and return the assistant reply.

        Args:
            message: Non-empty user message (validated at the API layer).

        Returns:
            The assistant response text, model name, and generation timestamp.

        Raises:
            OllamaConnectionError: If Ollama cannot be reached.
            OllamaResponseError: If Ollama returns an invalid response.
        """
        logger.info("chat_message_received", message_length=len(message))

        response_text = self._ollama.generate(message)
        result = ChatResult(
            response=response_text,
            model=self._ollama.model,
            timestamp=datetime.now(UTC),
        )

        logger.info(
            "chat_message_complete",
            model=result.model,
            response_length=len(result.response),
        )
        return result


@lru_cache(maxsize=1)
def get_chat_service() -> ChatService:
    """Return a cached `ChatService` built from `get_ollama_client()`.

    Use as a FastAPI dependency: `Depends(get_chat_service)`.
    """
    return ChatService(get_ollama_client())
