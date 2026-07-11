"""Abstract base class for all tools."""

from abc import ABC, abstractmethod
from typing import Any


class BaseTool(ABC):
    """Abstract base class representing a JarvisOS tool."""

    @property
    @abstractmethod
    def name(self) -> str:
        """The unique name identifier of the tool."""

    @property
    @abstractmethod
    def description(self) -> str:
        """A brief description explaining what the tool does and its purpose."""

    @abstractmethod
    def execute(self, **kwargs: Any) -> Any:
        """Execute the tool with the provided arguments.

        Args:
            **kwargs: Arbitrary keyword arguments needed for tool execution.

        Returns:
            The execution result.

        Raises:
            ToolError: If tool execution fails.
        """
