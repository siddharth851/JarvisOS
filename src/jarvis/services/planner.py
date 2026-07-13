"""Planner layer.

Validates intent+entities, selects the correct tool and prepares an execution
plan (but never executes tools).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from jarvis.services.intent_detection import DetectedIntent
from jarvis.services.entity_extraction import ExtractedEntities


@dataclass(frozen=True)
class PlannedTool:
    """A validated tool execution plan."""

    tool: str
    action: str
    arguments: dict[str, Any]


@dataclass(frozen=True)
class PlannedCommand:
    """Planner output including whether it should execute tools."""

    type: str  # "CHAT" | "TOOL"
    tool: str | None = None
    action: str | None = None
    arguments: dict[str, Any] = None  # type: ignore[assignment]


class CommandPlanner:
    """Validates and prepares the correct tool action."""

    def plan(
        self,
        detected_intent: DetectedIntent | None,
        extracted: ExtractedEntities,
        *,
        min_confidence: float = 0.75,
    ) -> PlannedCommand:
        if detected_intent is None:
            return PlannedCommand(type="CHAT")

        if detected_intent.confidence < min_confidence:
            return PlannedCommand(type="CHAT")

        entities = extracted.entities

        # Map intent -> tool/action (not hardcoded message strings).
        intent = detected_intent.intent

        if intent == "BROWSER_OPEN_GOOGLE":
            return PlannedCommand(
                type="TOOL",
                tool="browser",
                action="open_google",
                arguments={},
            )

        if intent == "BROWSER_OPEN_DESTINATION":
            destination = entities.get("destination")
            if not isinstance(destination, str) or not destination:
                return PlannedCommand(type="CHAT")
            return PlannedCommand(
                type="TOOL",
                tool="browser",
                action="open_destination",
                arguments={"destination": destination},
            )

        if intent == "BROWSER_OPEN_URL":
            url = entities.get("url")
            if not isinstance(url, str) or not url:
                return PlannedCommand(type="CHAT")
            return PlannedCommand(
                type="TOOL",
                tool="browser",
                action="open_url",
                arguments={"url": url},
            )

        if intent == "FILE_CREATE_FOLDER":
            # Backward-compatible behavior: allow empty suffix.
            path = entities.get("path")
            if not isinstance(path, str):
                return PlannedCommand(type="CHAT")
            return PlannedCommand(
                type="TOOL",
                tool="file",
                action="create_folder",
                arguments={"path": path},
            )

        if intent == "FILE_CREATE_FILE":
            # Backward-compatible behavior: allow empty suffix.
            path = entities.get("path")
            if not isinstance(path, str):
                return PlannedCommand(type="CHAT")
            return PlannedCommand(
                type="TOOL",
                tool="file",
                action="create_file",
                arguments={"path": path},
            )

        if intent == "FILE_READ_FILE":
            path = entities.get("path")
            if not isinstance(path, str) or not path:
                return PlannedCommand(type="CHAT")
            return PlannedCommand(
                type="TOOL",
                tool="file",
                action="read_file",
                arguments={"path": path},
            )

        if intent == "FILE_WRITE_FILE":
            path = entities.get("path")
            content = entities.get("content")
            if not isinstance(path, str) or not path or content is None:
                return PlannedCommand(type="CHAT")
            if not isinstance(content, str):
                # Coerce to str defensively
                content = str(content)
            return PlannedCommand(
                type="TOOL",
                tool="file",
                action="write_file",
                arguments={"path": path, "content": content},
            )

        if intent == "FILE_DELETE_FILE":
            path = entities.get("path")
            if not isinstance(path, str) or not path:
                return PlannedCommand(type="CHAT")
            return PlannedCommand(
                type="TOOL",
                tool="file",
                action="delete_file",
                arguments={"path": path},
            )

        if intent == "FILE_LIST_DIRECTORY":
            path = entities.get("path")
            if not isinstance(path, str) or not path:
                return PlannedCommand(type="CHAT")
            return PlannedCommand(
                type="TOOL",
                tool="file",
                action="list_directory",
                arguments={"path": path},
            )

        if intent == "TERMINAL_RUN":
            command = entities.get("command")
            if not isinstance(command, str) or not command:
                return PlannedCommand(type="CHAT")
            return PlannedCommand(
                type="TOOL",
                tool="terminal",
                action="run",
                arguments={"command": command},
            )

        return PlannedCommand(type="CHAT")
