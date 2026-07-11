import pytest
from pathlib import Path
from typing import Any

from jarvis.tools import ToolError, get_tool_registry
from jarvis.tools.file_tool import FileTool


def test_file_tool_properties() -> None:
    tool = FileTool()
    assert tool.name == "file_tool"
    assert isinstance(tool.description, str)
    assert len(tool.description) > 0


def test_path_validation() -> None:
    tool = FileTool()
    with pytest.raises(ToolError) as exc_info:
        tool._validate_path(None)
    assert "non-empty string" in str(exc_info.value)

    with pytest.raises(ToolError) as exc_info:
        tool._validate_path("")
    assert "non-empty string" in str(exc_info.value)

    with pytest.raises(ToolError) as exc_info:
        tool._validate_path(123)
    assert "non-empty string" in str(exc_info.value)


def test_create_folder(tmp_path: Path) -> None:
    tool = FileTool()
    folder_path = tmp_path / "new_folder"
    assert tool.create_folder(str(folder_path)) is True
    assert folder_path.exists()
    assert folder_path.is_dir()


def test_create_folder_nested(tmp_path: Path) -> None:
    tool = FileTool()
    folder_path = tmp_path / "parent" / "child"
    assert tool.create_folder(str(folder_path)) is True
    assert folder_path.exists()
    assert folder_path.is_dir()


def test_create_folder_failure(tmp_path: Path) -> None:
    tool = FileTool()
    # Create a file
    file_path = tmp_path / "some_file.txt"
    file_path.touch()
    # Try to create a folder where a file exists
    with pytest.raises(ToolError) as exc_info:
        tool.create_folder(str(file_path))
    assert "Failed to create folder" in str(exc_info.value)


def test_create_file(tmp_path: Path) -> None:
    tool = FileTool()
    file_path = tmp_path / "new_file.txt"
    assert tool.create_file(str(file_path)) is True
    assert file_path.exists()
    assert file_path.is_file()


def test_create_file_nested(tmp_path: Path) -> None:
    tool = FileTool()
    file_path = tmp_path / "parent" / "new_file.txt"
    assert tool.create_file(str(file_path)) is True
    assert file_path.exists()
    assert file_path.is_file()


def test_create_file_failure(tmp_path: Path) -> None:
    tool = FileTool()
    # Try to create a file with a path ending in / on Unix, or write to invalid path
    # We can pass an invalid directory parent path (e.g. if parent is a file)
    parent_file = tmp_path / "file_blocking"
    parent_file.touch()
    invalid_file_path = parent_file / "child.txt"

    with pytest.raises(ToolError) as exc_info:
        tool.create_file(str(invalid_file_path))
    assert "Failed to create file" in str(exc_info.value)


def test_write_and_read_file(tmp_path: Path) -> None:
    tool = FileTool()
    file_path = tmp_path / "test.txt"
    
    assert tool.write_file(str(file_path), "Hello World!") is True
    assert file_path.read_text(encoding="utf-8") == "Hello World!"

    assert tool.read_file(str(file_path)) == "Hello World!"


def test_write_file_invalid_content(tmp_path: Path) -> None:
    tool = FileTool()
    file_path = tmp_path / "test.txt"
    with pytest.raises(ToolError) as exc_info:
        tool.write_file(str(file_path), None)  # type: ignore[arg-type]
    assert "Content must be a string" in str(exc_info.value)


def test_read_file_not_found(tmp_path: Path) -> None:
    tool = FileTool()
    file_path = tmp_path / "non_existent.txt"
    with pytest.raises(ToolError) as exc_info:
        tool.read_file(str(file_path))
    assert "is not a file" in str(exc_info.value)


def test_read_file_is_directory(tmp_path: Path) -> None:
    tool = FileTool()
    with pytest.raises(ToolError) as exc_info:
        tool.read_file(str(tmp_path))
    assert "is not a file" in str(exc_info.value)


def test_delete_file(tmp_path: Path) -> None:
    tool = FileTool()
    file_path = tmp_path / "delete_me.txt"
    file_path.touch()
    
    assert tool.delete_file(str(file_path)) is True
    assert not file_path.exists()


def test_delete_file_not_found(tmp_path: Path) -> None:
    tool = FileTool()
    file_path = tmp_path / "non_existent.txt"
    with pytest.raises(ToolError) as exc_info:
        tool.delete_file(str(file_path))
    assert "does not exist" in str(exc_info.value)


def test_delete_file_is_directory(tmp_path: Path) -> None:
    tool = FileTool()
    with pytest.raises(ToolError) as exc_info:
        tool.delete_file(str(tmp_path))
    assert "is not a file" in str(exc_info.value)


def test_list_directory(tmp_path: Path) -> None:
    tool = FileTool()
    
    # Empty
    assert tool.list_directory(str(tmp_path)) == []

    # With files
    (tmp_path / "b.txt").touch()
    (tmp_path / "a.txt").touch()
    (tmp_path / "subdir").mkdir()

    assert tool.list_directory(str(tmp_path)) == ["a.txt", "b.txt", "subdir"]


def test_list_directory_not_directory(tmp_path: Path) -> None:
    tool = FileTool()
    file_path = tmp_path / "file.txt"
    file_path.touch()
    with pytest.raises(ToolError) as exc_info:
        tool.list_directory(str(file_path))
    assert "is not a directory" in str(exc_info.value)


def test_execute_create_folder(tmp_path: Path) -> None:
    tool = FileTool()
    path = tmp_path / "exec_folder"
    assert tool.execute(action="create_folder", path=str(path)) is True
    assert path.exists()


def test_execute_create_file(tmp_path: Path) -> None:
    tool = FileTool()
    path = tmp_path / "exec_file.txt"
    assert tool.execute(action="create_file", path=str(path)) is True
    assert path.exists()


def test_execute_write_and_read_file(tmp_path: Path) -> None:
    tool = FileTool()
    path = tmp_path / "exec_write.txt"
    assert tool.execute(action="write_file", path=str(path), content="Execute Content") is True
    assert tool.execute(action="read_file", path=str(path)) == "Execute Content"


def test_execute_delete_file(tmp_path: Path) -> None:
    tool = FileTool()
    path = tmp_path / "exec_delete.txt"
    path.touch()
    assert tool.execute(action="delete_file", path=str(path)) is True
    assert not path.exists()


def test_execute_list_directory(tmp_path: Path) -> None:
    tool = FileTool()
    (tmp_path / "test.txt").touch()
    assert tool.execute(action="list_directory", path=str(tmp_path)) == ["test.txt"]


def test_execute_missing_action() -> None:
    tool = FileTool()
    with pytest.raises(ToolError) as exc_info:
        tool.execute(path="some_path")
    assert "Missing 'action' parameter" in str(exc_info.value)


def test_execute_missing_path() -> None:
    tool = FileTool()
    with pytest.raises(ToolError) as exc_info:
        tool.execute(action="create_file")
    assert "Missing 'path' parameter" in str(exc_info.value)


def test_execute_write_file_missing_content(tmp_path: Path) -> None:
    tool = FileTool()
    with pytest.raises(ToolError) as exc_info:
        tool.execute(action="write_file", path=str(tmp_path / "file.txt"))
    assert "Missing 'content' parameter" in str(exc_info.value)


def test_execute_unsupported_action(tmp_path: Path) -> None:
    tool = FileTool()
    with pytest.raises(ToolError) as exc_info:
        tool.execute(action="invalid_action", path=str(tmp_path))
    assert "Unsupported action" in str(exc_info.value)


def test_automatic_registration() -> None:
    get_tool_registry.cache_clear()
    registry = get_tool_registry()
    tool = registry.get("file_tool")
    assert isinstance(tool, FileTool)
