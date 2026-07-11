"""Tool registry implementation."""

from functools import lru_cache
from jarvis.core.logging import get_logger
from jarvis.tools.base import BaseTool
from jarvis.tools.exceptions import ToolNotFoundError, ToolRegistrationError

logger = get_logger("jarvis.tools")


class ToolRegistry:
    """Registry to manage and lookup available tools."""

    def __init__(self) -> None:
        self._tools: dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        """Register a new tool instance in the registry.

        Args:
            tool: The BaseTool instance to register.

        Raises:
            ToolRegistrationError: If the tool is not a BaseTool instance
                                  or a tool with the same name already exists.
        """
        if not isinstance(tool, BaseTool):
            logger.error("tool_registration_failed_invalid_type", type=type(tool))
            raise ToolRegistrationError(f"Expected BaseTool instance, got {type(tool).__name__}")

        if tool.name in self._tools:
            logger.error("tool_registration_failed_duplicate", name=tool.name)
            raise ToolRegistrationError(f"Tool with name '{tool.name}' is already registered.")

        self._tools[tool.name] = tool
        logger.info("tool_registered", name=tool.name, description=tool.description)

    def unregister(self, name: str) -> None:
        """Remove a tool from the registry by its name.

        Args:
            name: The name of the tool to unregister.

        Raises:
            ToolNotFoundError: If no tool with the given name is registered.
        """
        if name not in self._tools:
            logger.error("tool_unregistration_failed_not_found", name=name)
            raise ToolNotFoundError(f"Tool '{name}' not found in registry.")

        del self._tools[name]
        logger.info("tool_unregistered", name=name)

    def get(self, name: str) -> BaseTool:
        """Retrieve a tool from the registry by its name.

        Args:
            name: The name of the tool to retrieve.

        Returns:
            The registered BaseTool instance.

        Raises:
            ToolNotFoundError: If no tool with the given name is registered.
        """
        if name not in self._tools:
            logger.debug("tool_lookup_failed_not_found", name=name)
            raise ToolNotFoundError(f"Tool '{name}' not found in registry.")

        return self._tools[name]

    def list_tools(self) -> list[BaseTool]:
        """List all currently registered tools.

        Returns:
            A list of all registered BaseTool instances.
        """
        return list(self._tools.values())


@lru_cache(maxsize=1)
def get_tool_registry() -> ToolRegistry:
    """Return a cached, singleton `ToolRegistry` instance."""
    registry = ToolRegistry()
    from jarvis.tools.browser import BrowserTool
    from jarvis.tools.file_tool import FileTool
    registry.register(BrowserTool())
    registry.register(FileTool())
    return registry
