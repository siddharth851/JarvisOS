"""Chat service.

Orchestrates user messages through the Ollama provider. Keeps HTTP concerns
in the API layer; this module owns chat business logic only.
"""

from dataclasses import dataclass
from datetime import UTC, datetime
from functools import lru_cache

from sqlalchemy import asc

from jarvis.core.logging import get_logger
from jarvis.database import SessionLocal
from jarvis.database.models import ChatMessage, ChatSession
from jarvis.providers.ollama import OllamaClient, get_ollama_client

logger = get_logger("jarvis.chat")


@dataclass(frozen=True)
class ChatResult:
    """Result of a single chat turn."""

    session_id: str
    response: str
    model: str
    timestamp: datetime


class ChatService:
    """Handles chat message processing via Ollama."""

    def __init__(self, ollama_client: OllamaClient) -> None:
        self._ollama = ollama_client

    def _load_conversation_history(self, db: object, session_id: str) -> list[str]:
        """Load all previous messages for a session and format as conversation context.

        Args:
            db: SQLAlchemy session object.
            session_id: The session identifier.

        Returns:
            List of formatted conversation lines in chronological order.
        """
        messages = (
            db.query(ChatMessage)
            .filter(ChatMessage.session_id == session_id)
            .order_by(asc(ChatMessage.created_at))
            .all()
        )

        context_lines = []
        for msg in messages:
            if msg.role == "user":
                context_lines.append(f"User: {msg.content}")
            elif msg.role == "assistant":
                context_lines.append(f"Assistant: {msg.content}")

        return context_lines

    def _build_full_prompt(self, history: list[str], current_message: str) -> str:
        """Build the full prompt from conversation history and current message.

        Args:
            history: List of formatted previous messages.
            current_message: The current user message.

        Returns:
            The full prompt to send to the AI model.
        """
        if not history:
            return current_message

        return "\n".join(history) + f"\nUser: {current_message}"

    def chat(self, message: str, session_id: str | None = None) -> ChatResult:
        """Send a user message to Ollama and persist the chat session.

        Args:
            message: Non-empty user message (validated at the API layer).
            session_id: Optional existing session identifier.

        Returns:
            The session identifier, assistant response text, model name, and
            generation timestamp.

        Raises:
            OllamaConnectionError: If Ollama cannot be reached.
            OllamaResponseError: If Ollama returns an invalid response.
        """
        logger.info("chat_message_received", message_length=len(message))

        from jarvis.database import SessionLocal

        with SessionLocal() as db:
            session = None
            if session_id is not None:
                session = db.get(ChatSession, session_id)

            if session is None:
                session = ChatSession()
                db.add(session)
                db.flush()

            session.updated_at = datetime.now(UTC)

            history = self._load_conversation_history(db, session.id)
            full_prompt = self._build_full_prompt(history, message)

            logger.info(
                "chat_history_loaded",
                session_id=session.id,
                history_length=len(history),
            )

            user_message = ChatMessage(
                session_id=session.id,
                role="user",
                content=message,
            )
            db.add(user_message)
            db.flush()

            response_text = self._ollama.generate(full_prompt)

            assistant_message = ChatMessage(
                session_id=session.id,
                role="assistant",
                content=response_text,
            )
            db.add(assistant_message)
            db.commit()

            # Capture the session ID before the context closes
            result_session_id = session.id

        result = ChatResult(
            session_id=result_session_id,
            response=response_text,
            model=self._ollama.model,
            timestamp=datetime.now(UTC),
        )

        logger.info(
            "chat_message_complete",
            session_id=result.session_id,
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
