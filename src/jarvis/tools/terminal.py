"""Terminal tool implementation."""

import shlex
import subprocess
from typing import Any

from jarvis.tools.base import BaseTool
from jarvis.tools.exceptions import ToolError


class TerminalTool(BaseTool):
    """Tool for running terminal commands."""

    @property
    def name(self) -> str:
        """The unique name identifier of the tool."""
        return "terminal_tool"

    @property
    def description(self) -> str:
        """A brief description explaining what the tool does and its purpose."""
        return "A tool to execute terminal commands."

    def run(self, command: str) -> dict[str, Any]:
        """Run a terminal command.

        Args:
            command: The command string to execute.

        Returns:
            A dict containing success (bool), stdout (str), stderr (str), and exit_code (int).

        Raises:
            ToolError: If command is invalid or execution fails.
        """
        if not command or not isinstance(command, str):
            raise ToolError("Command must be a non-empty string")

        try:
            # Parse command string into list of arguments safely
            args = shlex.split(command)
        except Exception as e:
            raise ToolError(f"Failed to parse command '{command}': {e}")

        if not args:
            raise ToolError("Parsed command arguments list is empty")

        try:
            result = subprocess.run(
                args,
                capture_output=True,
                text=True,
                shell=False,
                check=False,
            )
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "exit_code": result.returncode,
            }
        except FileNotFoundError as e:
            # Command binary not found
            raise ToolError(f"Command not found: '{args[0]}'") from e
        except Exception as e:
            raise ToolError(f"Failed to execute command '{command}': {e}") from e

    def execute(self, **kwargs: Any) -> Any:
        """Execute the terminal tool action.

        Args:
            action: The action to perform (must be "run").
            command: The command string to execute (required).

        Returns:
            A dict containing success (bool), stdout (str), stderr (str), and exit_code (int).

        Raises:
            ToolError: If action is missing, unsupported, or if parameters are invalid.
        """
        action = kwargs.get("action")
        if not action:
            raise ToolError("Missing 'action' parameter for terminal_tool")

        if action != "run":
            raise ToolError(f"Unsupported action: '{action}'")

        command = kwargs.get("command")
        if command is None:
            raise ToolError("Missing 'command' parameter for 'run' action")

        return self.run(command)
