"""File tool implementation."""

import os
from pathlib import Path
from typing import Any

from jarvis.tools.base import BaseTool
from jarvis.tools.exceptions import ToolError


class FileTool(BaseTool):
    """Tool for performing local filesystem actions."""

    @property
    def name(self) -> str:
        """The unique name identifier of the tool."""
        return "file_tool"

    @property
    def description(self) -> str:
        """A brief description explaining what the tool does and its purpose."""
        return "A tool to create, read, write, delete files/folders and list directories."

    def _validate_path(self, path: Any) -> Path:
        """Validate that the path is a non-empty string and return a Path object.

        Args:
            path: The path input to validate.

        Returns:
            A Path object representing the path.

        Raises:
            ToolError: If the path is empty, not a string, or invalid.
        """
        if not path or not isinstance(path, str):
            raise ToolError("Path must be a non-empty string")
        try:
            return Path(path)
        except Exception as e:
            raise ToolError(f"Invalid path format: {e}")

    def create_folder(self, path: str) -> bool:
        """Create a directory (and any parent directories) at the given path.

        Args:
            path: The directory path to create.

        Returns:
            True if folder creation was successful.

        Raises:
            ToolError: If folder creation fails.
        """
        p = self._validate_path(path)
        try:
            p.mkdir(parents=True, exist_ok=True)
            return True
        except Exception as e:
            raise ToolError(f"Failed to create folder '{path}': {e}")

    def create_file(self, path: str) -> bool:
        """Create an empty file at the given path.

        Args:
            path: The file path to create.

        Returns:
            True if file creation was successful.

        Raises:
            ToolError: If file creation fails.
        """
        p = self._validate_path(path)
        try:
            if p.parent:
                p.parent.mkdir(parents=True, exist_ok=True)
            p.touch(exist_ok=True)
            return True
        except Exception as e:
            raise ToolError(f"Failed to create file '{path}': {e}")

    def read_file(self, path: str) -> str:
        """Read the contents of a file as a string.

        Args:
            path: The path of the file to read.

        Returns:
            The content of the file.

        Raises:
            ToolError: If reading fails or the path is a directory.
        """
        p = self._validate_path(path)
        try:
            if not p.is_file():
                raise ToolError(f"Path '{path}' is not a file")
            return p.read_text(encoding="utf-8")
        except ToolError:
            raise
        except Exception as e:
            raise ToolError(f"Failed to read file '{path}': {e}")

    def write_file(self, path: str, content: str) -> bool:
        """Write string content to a file at the given path.

        Args:
            path: The file path to write to.
            content: The text content to write.

        Returns:
            True if write was successful.

        Raises:
            ToolError: If writing fails.
        """
        p = self._validate_path(path)
        if not isinstance(content, str):
            raise ToolError("Content must be a string")
        try:
            if p.parent:
                p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content, encoding="utf-8")
            return True
        except Exception as e:
            raise ToolError(f"Failed to write to file '{path}': {e}")

    def delete_file(self, path: str) -> bool:
        """Delete a file at the given path.

        Args:
            path: The file path to delete.

        Returns:
            True if deletion was successful.

        Raises:
            ToolError: If deletion fails or path is a directory.
        """
        p = self._validate_path(path)
        try:
            if not p.exists():
                raise ToolError(f"File '{path}' does not exist")
            if not p.is_file():
                raise ToolError(f"Path '{path}' is not a file")
            p.unlink()
            return True
        except ToolError:
            raise
        except Exception as e:
            raise ToolError(f"Failed to delete file '{path}': {e}")

    def list_directory(self, path: str) -> list[str]:
        """List the names of contents in a directory at the given path.

        Args:
            path: The directory path to list.

        Returns:
            A sorted list of file and directory names.

        Raises:
            ToolError: If listing fails or path is not a directory.
        """
        p = self._validate_path(path)
        try:
            if not p.is_dir():
                raise ToolError(f"Path '{path}' is not a directory")
            return sorted(os.listdir(p))
        except ToolError:
            raise
        except Exception as e:
            raise ToolError(f"Failed to list directory '{path}': {e}")

    def execute(self, **kwargs: Any) -> Any:
        """Execute the requested file action.

        Args:
            action: The action to perform (e.g. "create_file").
            path: The path target of the action.
            content: Required only for "write_file".

        Returns:
            The execution result.

        Raises:
            ToolError: On unsupported action or invalid arguments.
        """
        action = kwargs.get("action")
        if not action:
            raise ToolError("Missing 'action' parameter for file_tool")

        path = kwargs.get("path")
        if path is None:
            raise ToolError(f"Missing 'path' parameter for '{action}' action")

        if action == "create_folder":
            return self.create_folder(path)

        elif action == "create_file":
            return self.create_file(path)

        elif action == "read_file":
            return self.read_file(path)

        elif action == "write_file":
            content = kwargs.get("content")
            if content is None:
                raise ToolError("Missing 'content' parameter for 'write_file' action")
            return self.write_file(path, content)

        elif action == "delete_file":
            return self.delete_file(path)

        # New higher-level operations that return structured responses via FileManager
        from jarvis.services.file_manager import get_file_manager

        manager = get_file_manager()

        if action == "open":
            # open may refer to a file or folder; try file first, then folder
            file_resp = manager.open_file(path)
            if file_resp["status"] == "success":
                return file_resp
            return manager.open_folder(path)

        if action == "open_folder":
            return manager.open_folder(path)

        if action == "rename":
            dst = kwargs.get("dst")
            if not dst or not isinstance(dst, str):
                raise ToolError("Missing 'dst' parameter for 'rename' action")
            return manager.rename(path, dst)

        if action == "move":
            dst = kwargs.get("dst")
            if not dst or not isinstance(dst, str):
                raise ToolError("Missing 'dst' parameter for 'move' action")
            return manager.move(path, dst)

        if action == "copy":
            dst = kwargs.get("dst")
            if not dst or not isinstance(dst, str):
                raise ToolError("Missing 'dst' parameter for 'copy' action")
            return manager.copy(path, dst)

        if action == "delete":
            return manager.delete(path)

        elif action == "list_directory":
            return self.list_directory(path)

        else:
            raise ToolError(f"Unsupported action: '{action}'")
