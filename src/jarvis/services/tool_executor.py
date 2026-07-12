"""Tool Executor Service."""

from typing import Any

from jarvis.services.command_router import RoutingResult
from jarvis.tools.exceptions import ToolError, ToolNotFoundError
from jarvis.tools.registry import ToolRegistry, get_tool_registry


class ToolExecutor:
    """Executes routed tool commands using the ToolRegistry."""

    def __init__(self, registry: ToolRegistry | None = None) -> None:
        """Initialize the executor.

        Args:
            registry: Optional custom ToolRegistry instance.
                      Defaults to the singleton get_tool_registry().
        """
        self._registry = registry or get_tool_registry()
        # Map short name identifiers to full registered names
        self._tool_map = {
            "browser": "browser_tool",
            "file": "file_tool",
            "terminal": "terminal_tool",
        }

    def execute(self, routing_result: RoutingResult) -> dict[str, Any] | None:
        """Execute a tool action based on the routing classification.

        Args:
            routing_result: The classification result from the CommandRouter.

        Returns:
            A dictionary containing success, tool name, and result/error,
            or None if the routing type is CHAT.
        """
        if not routing_result or routing_result.type == "CHAT":
            return None

        tool_name = routing_result.tool
        action = routing_result.action
        arguments = routing_result.arguments or {}

        # Resolve registered name
        registered_name = self._tool_map.get(tool_name, tool_name)

        try:
            if not registered_name:
                raise ToolNotFoundError("No tool specified in routing result")

            tool = self._registry.get(registered_name)
            result = tool.execute(action=action, **arguments)

            return {
                "success": True,
                "tool": tool_name,
                "result": result,
            }
        except ToolNotFoundError as e:
            return {
                "success": False,
                "tool": tool_name,
                "error": f"Tool '{tool_name}' not found: {e}",
            }
        except ToolError as e:
            return {
                "success": False,
                "tool": tool_name,
                "error": str(e),
            }
        except Exception as e:
            return {
                "success": False,
                "tool": tool_name,
                "error": f"Unexpected execution failure: {e}",
            }
