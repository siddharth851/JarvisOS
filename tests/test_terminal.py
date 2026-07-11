import sys
import pytest
from typing import Any

from jarvis.tools import ToolError, get_tool_registry
from jarvis.tools.terminal import TerminalTool


def test_terminal_tool_properties() -> None:
    tool = TerminalTool()
    assert tool.name == "terminal_tool"
    assert isinstance(tool.description, str)
    assert len(tool.description) > 0


def test_run_success() -> None:
    tool = TerminalTool()
    # Use python executable to run a cross-platform command
    cmd = f'{sys.executable} -c "print(\'hello\')"'
    res = tool.run(cmd)
    
    assert res["success"] is True
    assert "hello" in res["stdout"]
    assert res["stderr"].strip() == ""
    assert res["exit_code"] == 0


def test_run_failing_exit_code() -> None:
    tool = TerminalTool()
    # Command that exits with non-zero code
    cmd = f'{sys.executable} -c "import sys; sys.exit(42)"'
    res = tool.run(cmd)
    
    assert res["success"] is False
    assert res["exit_code"] == 42


def test_run_non_existent_command() -> None:
    tool = TerminalTool()
    with pytest.raises(ToolError) as exc_info:
        tool.run("somefakecommand123456789")
    assert "Command not found" in str(exc_info.value)


def test_run_invalid_command_input() -> None:
    tool = TerminalTool()
    # Empty command
    with pytest.raises(ToolError) as exc_info:
        tool.run("")
    assert "non-empty string" in str(exc_info.value)

    # None command
    with pytest.raises(ToolError) as exc_info:
        tool.run(None)  # type: ignore[arg-type]
    assert "non-empty string" in str(exc_info.value)


def test_execute_run() -> None:
    tool = TerminalTool()
    cmd = f'{sys.executable} -c "print(\'execute_test\')"'
    res = tool.execute(action="run", command=cmd)
    
    assert res["success"] is True
    assert "execute_test" in res["stdout"]
    assert res["exit_code"] == 0


def test_execute_missing_action() -> None:
    tool = TerminalTool()
    with pytest.raises(ToolError) as exc_info:
        tool.execute(command="echo hello")
    assert "Missing 'action' parameter" in str(exc_info.value)


def test_execute_unsupported_action() -> None:
    tool = TerminalTool()
    with pytest.raises(ToolError) as exc_info:
        tool.execute(action="invalid_action", command="echo hello")
    assert "Unsupported action" in str(exc_info.value)


def test_execute_missing_command() -> None:
    tool = TerminalTool()
    with pytest.raises(ToolError) as exc_info:
        tool.execute(action="run")
    assert "Missing 'command' parameter" in str(exc_info.value)


def test_automatic_registration() -> None:
    get_tool_registry.cache_clear()
    registry = get_tool_registry()
    tool = registry.get("terminal_tool")
    assert isinstance(tool, TerminalTool)
