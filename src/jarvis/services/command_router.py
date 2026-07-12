"""Command Router Service.

Public API: `CommandRouter.route(message) -> RoutingResult`.

Internally delegates to the modular AI OS pipeline.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

from jarvis.services.ai_os_command_pipeline import AIOSCommandPipeline
from jarvis.services.tool_registry_adapter import ToolRegistryAdapter


@dataclass(frozen=True)
class RoutingResult:
    """Represents the structured classification output of the Command Router."""

    type: Literal["CHAT", "TOOL"]
    tool: str | None = None
    action: str | None = None
    arguments: dict[str, Any] = field(default_factory=dict)


class CommandRouter:
    """Routes incoming user messages to either CHAT or a specific TOOL action."""

    def __init__(self) -> None:
        self._pipeline = AIOSCommandPipeline()
        self._adapter = ToolRegistryAdapter()

    def route(self, message: str) -> RoutingResult:
        """Classify user message into CHAT or TOOL type."""
        if not message or not isinstance(message, str):
            return RoutingResult(type="CHAT")

        planned_result = self._pipeline.process(message).planned
        return self._adapter.to_routing_result(planned_result)
