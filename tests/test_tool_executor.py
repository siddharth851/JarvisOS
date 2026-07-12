import sys
from pathlib import Path
from unittest.mock import patch
import pytest
from typing import Any

from jarvis.services.command_router import RoutingResult
from jarvis.services.tool_executor import ToolExecutor


def test_executor_chat_routing_returns_none() -> None:
    executor = ToolExecutor()
    res = executor.execute(RoutingResult(type="CHAT"))
    assert res is None


@patch("webbrowser.open")
def test_executor_browser_execution(mock_open: Any) -> None:
    mock_open.return_value = True
    executor = ToolExecutor()
    
    routing = RoutingResult(
        type="TOOL",
        tool="browser",
        action="open_google",
        arguments={},
    )
    res = executor.execute(routing)
    
    assert res is not None
    assert res["success"] is True
    assert res["tool"] == "browser"
    assert res["result"] is True
    mock_open.assert_called_once_with("https://google.com")


def test_executor_file_execution(tmp_path: Path) -> None:
    executor = ToolExecutor()
    file_path = tmp_path / "test.txt"
    
    routing = RoutingResult(
        type="TOOL",
        tool="file",
        action="write_file",
        arguments={"path": str(file_path), "content": "hello executor"},
    )
    res = executor.execute(routing)
    
    assert res is not None
    assert res["success"] is True
    assert res["tool"] == "file"
    assert res["result"] is True
    assert file_path.read_text(encoding="utf-8") == "hello executor"


def test_executor_terminal_execution() -> None:
    executor = ToolExecutor()
    cmd = f'{sys.executable} -c "print(\'executor_ok\')"'
    
    routing = RoutingResult(
        type="TOOL",
        tool="terminal",
        action="run",
        arguments={"command": cmd},
    )
    res = executor.execute(routing)
    
    assert res is not None
    assert res["success"] is True
    assert res["tool"] == "terminal"
    assert res["result"]["success"] is True
    assert "executor_ok" in res["result"]["stdout"]


def test_executor_unknown_tool() -> None:
    executor = ToolExecutor()
    
    routing = RoutingResult(
        type="TOOL",
        tool="unknown_tool_xyz",
        action="do_something",
        arguments={},
    )
    res = executor.execute(routing)
    
    assert res is not None
    assert res["success"] is False
    assert res["tool"] == "unknown_tool_xyz"
    assert "not found" in res["error"]


def test_executor_tool_error_handling() -> None:
    executor = ToolExecutor()
    
    # Executing browser tool with invalid action raises ToolError
    routing = RoutingResult(
        type="TOOL",
        tool="browser",
        action="invalid_action",
        arguments={},
    )
    res = executor.execute(routing)
    
    assert res is not None
    assert res["success"] is False
    assert res["tool"] == "browser"
    assert "Unsupported action" in res["error"]
