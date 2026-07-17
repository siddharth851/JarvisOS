"""Application Tool wrapper.

This tool delegates application name resolution to the existing
ApplicationResolver and executes lifecycle actions through the
ApplicationManager.
"""

from typing import Any

from jarvis.tools.base import BaseTool
from jarvis.tools.exceptions import ToolError


class ApplicationTool(BaseTool):
    """Tool facade for application lifecycle operations."""

    @property
    def name(self) -> str:
        return "application_tool"

    @property
    def description(self) -> str:
        return (
            "A tool to resolve installed desktop applications and perform "
            "launch, close, and focus actions through the OS."
        )

    def execute(self, **kwargs: Any) -> Any:
        action = kwargs.get("action")
        if not action or not isinstance(action, str):
            raise ToolError("Missing 'action' parameter for application_tool")

        application = kwargs.get("application")
        if not application or not isinstance(application, str):
            raise ToolError("Missing 'application' parameter for application_tool")

        from jarvis.services.application_resolver import (
            ApplicationResolutionError,
            get_application_resolver,
        )
        from jarvis.services.application_manager import get_application_manager

        resolver = get_application_resolver()
        try:
            candidate = resolver.resolve(application)
        except ApplicationResolutionError as exc:
            raise ToolError(f"Application resolution failed: {exc}")

        if candidate.confidence < 0.35:
            raise ToolError(
                "Application match confidence too low. Please be more specific."
            )

        manager = get_application_manager()
        target = candidate.identifier

        if action == "launch":
            result = manager.launch(candidate.executable_path or target)
        elif action == "close":
            result = manager.close(target)
        elif action == "focus":
            result = manager.focus(target)
        else:
            raise ToolError(f"Unsupported action: '{action}' for application_tool")

        result.setdefault("data", {})
        result["data"]["resolved_application"] = {
            "resource_type": candidate.resource_type,
            "display_name": candidate.display_name,
            "identifier": candidate.identifier,
            "confidence": candidate.confidence,
            "running_state": candidate.running_state,
            "executable_path": candidate.executable_path,
        }
        return result