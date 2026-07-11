"""Chat endpoint."""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, field_validator

from jarvis.providers.ollama import OllamaConnectionError, OllamaResponseError
from jarvis.services.chat import ChatService, get_chat_service

router = APIRouter(tags=["chat"])


class ChatRequest(BaseModel):
    """Request body for `POST /chat`."""

    message: str = Field(min_length=1)

    @field_validator("message", mode="before")
    @classmethod
    def strip_whitespace(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip()
        return value


class ChatResponse(BaseModel):
    """Response body for `POST /chat`."""

    response: str
    model: str
    timestamp: datetime


@router.post("/chat", response_model=ChatResponse)
async def post_chat(
    body: ChatRequest,
    chat_service: ChatService = Depends(get_chat_service),
) -> ChatResponse:
    """Send a message and receive an Ollama-generated reply."""
    try:
        result = chat_service.chat(body.message)
    except OllamaConnectionError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Ollama service unavailable",
        ) from exc
    except OllamaResponseError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Ollama returned an invalid response",
        ) from exc

    return ChatResponse(
        response=result.response,
        model=result.model,
        timestamp=result.timestamp,
    )
