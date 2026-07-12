"""Command Router Service."""

from dataclasses import dataclass, field
from typing import Any, Literal


@dataclass(frozen=True)
class RoutingResult:
    """Represents the structured classification output of the Command Router."""

    type: Literal["CHAT", "TOOL"]
    tool: str | None = None
    action: str | None = None
    arguments: dict[str, Any] = field(default_factory=dict)


def _match_prefix(message: str, prefix: str) -> tuple[bool, str]:
    """Check if message starts with prefix (case-insensitive).

    Validates that prefix is followed by space, or it's a complete match.
    Preserves original case of the trailing argument string (suffix).

    Args:
        message: The original user message.
        prefix: The prefix pattern to match.

    Returns:
        A tuple of (is_match, suffix).
    """
    msg_lower = message.lower()
    pref_lower = prefix.lower()

    if msg_lower == pref_lower:
        return True, ""
    if msg_lower.startswith(pref_lower + " "):
        return True, message[len(prefix) + 1:].strip()
    return False, ""


class CommandRouter:
    """Routes incoming user messages to either CHAT or a specific TOOL action."""

    def route(self, message: str) -> RoutingResult:
        """Classify user message into CHAT or TOOL type.

        Args:
            message: The raw user message.

        Returns:
            A RoutingResult containing the classification and metadata.
        """
        if not message or not isinstance(message, str):
            return RoutingResult(type="CHAT")

        message = message.strip()

        # 1. Browser Tool
        matched, suffix = _match_prefix(message, "open google")
        if matched:
            return RoutingResult(type="TOOL", tool="browser", action="open_google")

        matched, suffix = _match_prefix(message, "open website")
        if matched:
            return RoutingResult(type="TOOL", tool="browser", action="open_url", arguments={"url": suffix})

        matched, suffix = _match_prefix(message, "open url")
        if matched:
            return RoutingResult(type="TOOL", tool="browser", action="open_url", arguments={"url": suffix})

        # 2. File Tool
        matched, suffix = _match_prefix(message, "create folder")
        if matched:
            return RoutingResult(type="TOOL", tool="file", action="create_folder", arguments={"path": suffix})

        matched, suffix = _match_prefix(message, "create file")
        if matched:
            return RoutingResult(type="TOOL", tool="file", action="create_file", arguments={"path": suffix})

        matched, suffix = _match_prefix(message, "read file")
        if matched:
            return RoutingResult(type="TOOL", tool="file", action="read_file", arguments={"path": suffix})

        matched, suffix = _match_prefix(message, "write file")
        if matched:
            parts = suffix.split(maxsplit=1)
            path = parts[0] if len(parts) > 0 else ""
            content = parts[1] if len(parts) > 1 else ""
            return RoutingResult(
                type="TOOL",
                tool="file",
                action="write_file",
                arguments={"path": path, "content": content},
            )

        matched, suffix = _match_prefix(message, "delete file")
        if matched:
            return RoutingResult(type="TOOL", tool="file", action="delete_file", arguments={"path": suffix})

        matched, suffix = _match_prefix(message, "list directory")
        if matched:
            return RoutingResult(type="TOOL", tool="file", action="list_directory", arguments={"path": suffix})

        # 3. Terminal Tool
        matched, suffix = _match_prefix(message, "run")
        if matched:
            return RoutingResult(type="TOOL", tool="terminal", action="run", arguments={"command": suffix})

        matched, suffix = _match_prefix(message, "execute")
        if matched:
            return RoutingResult(type="TOOL", tool="terminal", action="run", arguments={"command": suffix})

        matched, suffix = _match_prefix(message, "terminal")
        if matched:
            return RoutingResult(type="TOOL", tool="terminal", action="run", arguments={"command": suffix})

        # Fallback to CHAT
        return RoutingResult(type="CHAT")
