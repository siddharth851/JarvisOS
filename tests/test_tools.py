import pytest
from typing import Any

from jarvis.tools import (
    BaseTool,
    ToolError,
    ToolNotFoundError,
    ToolRegistrationError,
    ToolRegistry,
    get_tool_registry,
)


class SimpleTestTool(BaseTool):
    """A simple tool implementation for testing."""

    @property
    def name(self) -> str:
        return "simple_test_tool"

    @property
    def description(self) -> str:
        return "A test tool that echoes input"

    def execute(self, **kwargs: Any) -> Any:
        if "fail" in kwargs and kwargs["fail"]:
            raise ToolError("Execution failed as requested")
        return kwargs.get("value", "default_value")


def test_base_tool_abstract() -> None:
    # Cannot instantiate BaseTool directly
    with pytest.raises(TypeError):
        BaseTool()  # type: ignore[abstract]


def test_tool_subclass_instantiation() -> None:
    tool = SimpleTestTool()
    assert tool.name == "simple_test_tool"
    assert tool.description == "A test tool that echoes input"
    assert tool.execute(value="hello") == "hello"


def test_tool_registry_registration() -> None:
    registry = ToolRegistry()
    tool = SimpleTestTool()

    # Initial state
    assert len(registry.list_tools()) == 0

    # Register
    registry.register(tool)
    assert len(registry.list_tools()) == 1
    assert registry.get("simple_test_tool") is tool

    # Prevent duplicate registration
    with pytest.raises(ToolRegistrationError) as exc_info:
        registry.register(tool)
    assert "already registered" in str(exc_info.value)


def test_tool_registry_invalid_registration() -> None:
    registry = ToolRegistry()

    # Cannot register non-BaseTool
    with pytest.raises(ToolRegistrationError) as exc_info:
        registry.register("not a tool")  # type: ignore[arg-type]
    assert "Expected BaseTool instance" in str(exc_info.value)


def test_tool_registry_get_not_found() -> None:
    registry = ToolRegistry()
    with pytest.raises(ToolNotFoundError) as exc_info:
        registry.get("non_existent")
    assert "not found in registry" in str(exc_info.value)


def test_tool_registry_unregister() -> None:
    registry = ToolRegistry()
    tool = SimpleTestTool()

    registry.register(tool)
    assert registry.get("simple_test_tool") is tool

    # Unregister
    registry.unregister("simple_test_tool")
    assert len(registry.list_tools()) == 0

    # Subsequent lookup fails
    with pytest.raises(ToolNotFoundError):
        registry.get("simple_test_tool")


def test_tool_registry_unregister_not_found() -> None:
    registry = ToolRegistry()
    with pytest.raises(ToolNotFoundError) as exc_info:
        registry.unregister("non_existent")
    assert "not found in registry" in str(exc_info.value)


def test_tool_registry_list_tools() -> None:
    registry = ToolRegistry()

    class AnotherTestTool(BaseTool):
        @property
        def name(self) -> str:
            return "another_tool"

        @property
        def description(self) -> str:
            return "Another test tool"

        def execute(self, **kwargs: Any) -> Any:
            return "another"

    tool1 = SimpleTestTool()
    tool2 = AnotherTestTool()

    registry.register(tool1)
    registry.register(tool2)

    tools = registry.list_tools()
    assert len(tools) == 2
    assert tool1 in tools
    assert tool2 in tools


def test_get_tool_registry_cached() -> None:
    get_tool_registry.cache_clear()
    first = get_tool_registry()
    second = get_tool_registry()
    assert first is second
    assert isinstance(first, ToolRegistry)
