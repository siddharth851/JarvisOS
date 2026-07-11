import pytest
from unittest.mock import patch
from typing import Any

from jarvis.tools import ToolError, get_tool_registry
from jarvis.tools.browser import BrowserTool


def test_browser_tool_properties() -> None:
    tool = BrowserTool()
    assert tool.name == "browser_tool"
    assert isinstance(tool.description, str)
    assert len(tool.description) > 0


@patch("webbrowser.open")
def test_open_url_success(mock_open: Any) -> None:
    mock_open.return_value = True
    tool = BrowserTool()
    assert tool.open_url("https://example.com") is True
    mock_open.assert_called_once_with("https://example.com")


def test_open_url_empty_raises() -> None:
    tool = BrowserTool()
    with pytest.raises(ToolError) as exc_info:
        tool.open_url("")
    assert "URL cannot be empty" in str(exc_info.value)


def test_open_url_invalid_protocol_raises() -> None:
    tool = BrowserTool()
    with pytest.raises(ToolError) as exc_info:
        tool.open_url("ftp://example.com")
    assert "Must start with 'http://' or 'https://'" in str(exc_info.value)


@patch("webbrowser.open")
def test_open_url_failure_raises(mock_open: Any) -> None:
    mock_open.side_effect = Exception("Some system error")
    tool = BrowserTool()
    with pytest.raises(ToolError) as exc_info:
        tool.open_url("https://example.com")
    assert "Failed to open URL" in str(exc_info.value)


@patch("webbrowser.open")
def test_open_google(mock_open: Any) -> None:
    mock_open.return_value = True
    tool = BrowserTool()
    assert tool.open_google() is True
    mock_open.assert_called_once_with("https://google.com")


@patch("webbrowser.open")
def test_execute_open_url(mock_open: Any) -> None:
    mock_open.return_value = True
    tool = BrowserTool()
    assert tool.execute(action="open_url", url="https://test.com") is True
    mock_open.assert_called_once_with("https://test.com")


def test_execute_open_url_missing_url() -> None:
    tool = BrowserTool()
    with pytest.raises(ToolError) as exc_info:
        tool.execute(action="open_url")
    assert "Missing 'url' parameter" in str(exc_info.value)


@patch("webbrowser.open")
def test_execute_open_google(mock_open: Any) -> None:
    mock_open.return_value = True
    tool = BrowserTool()
    assert tool.execute(action="open_google") is True
    mock_open.assert_called_once_with("https://google.com")


def test_execute_missing_action() -> None:
    tool = BrowserTool()
    with pytest.raises(ToolError) as exc_info:
        tool.execute()
    assert "Missing 'action' parameter" in str(exc_info.value)


def test_execute_unsupported_action() -> None:
    tool = BrowserTool()
    with pytest.raises(ToolError) as exc_info:
        tool.execute(action="unsupported_action")
    assert "Unsupported action" in str(exc_info.value)


def test_automatic_registration() -> None:
    get_tool_registry.cache_clear()
    registry = get_tool_registry()
    tool = registry.get("browser_tool")
    assert isinstance(tool, BrowserTool)
