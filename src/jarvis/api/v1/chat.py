"""Chat endpoint."""

from datetime import datetime
from typing import Any, Optional, Union

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, field_validator

from jarvis.providers.ollama import OllamaConnectionError, OllamaResponseError
from jarvis.services.chat import ChatResult, ChatService, get_chat_service
from jarvis.services.command_router import CommandRouter
from jarvis.services.tool_executor import ToolExecutor

router = APIRouter(tags=["chat"])


class ChatRequest(BaseModel):
    """Request body for `POST /chat`."""

    message: str = Field(min_length=1)
    session_id: Optional[str] = None

    @field_validator("message", mode="before")
    @classmethod
    def strip_whitespace(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip()
        return value

    @field_validator("session_id", mode="before")
    @classmethod
    def strip_session_id(cls, value: object) -> object:
        if isinstance(value, str):
            stripped = value.strip()
            return stripped or None
        return value


class ChatResponse(BaseModel):
    """Response body for `POST /chat` (AI conversation)."""

    session_id: str
    response: str
    model: str
    timestamp: datetime


class ToolResponse(BaseModel):
    """Response body for `POST /chat` (tool execution)."""

    type: str = Field(default="tool")
    session_id: str
    tool: str
    status: str  # "success" | "error"
    message: str
    data: dict[str, Any] = Field(default_factory=dict)


@router.post("/chat", response_model=Union[ChatResponse, ToolResponse])
async def post_chat(
    body: ChatRequest,
    chat_service: ChatService = Depends(get_chat_service),
):
    """Route the message to either a tool execution path or Ollama chat."""

    command_router = CommandRouter()
    tool_executor = ToolExecutor()
    routing = command_router.route(body.message)

    # TOOL path
    if routing.type == "TOOL":
        tool_result = tool_executor.execute(routing)  # always non-None for TOOL

        # Preserve provided session_id; otherwise generate a new one for frontend tracking.
        if body.session_id:
            session_id = body.session_id
        else:
            import uuid

            session_id = str(uuid.uuid4())

        assert tool_result is not None
        if tool_result.get("success") is True:
            return ToolResponse(
                type="tool",
                session_id=session_id,
                tool=str(tool_result.get("tool") or ""),
                status="success",
                message="Tool executed successfully.",
                data={"result": tool_result.get("result")},
            )

        return ToolResponse(
            type="tool",
            session_id=session_id,
            tool=str(tool_result.get("tool") or ""),
            status="error",
            message=str(tool_result.get("error") or "Tool execution failed."),
            data={},
        )

    # CHAT path (existing behavior)
    try:
        result = chat_service.chat(body.message, session_id=body.session_id)
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
        session_id=result.session_id,
        response=result.response,
        model=result.model,
        timestamp=result.timestamp,
    )
