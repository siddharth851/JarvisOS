"""Tests for browser automation: session, handlers, registry, and tool dispatch."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from jarvis.tools.browser import BrowserTool
from jarvis.tools.browser_automation.actions.registry import get_action_registry
from jarvis.tools.browser_automation.result import BrowserActionResult
from jarvis.tools.browser_automation.state import BrowserSession, get_browser_session


SAMPLE_HTML = """
<html>
<head><title>Test Page</title></head>
<body>
  <script>ignore me</script>
  <p>Hello world from Jarvis.</p>
  <p>Second paragraph here.</p>
</body>
</html>
"""

SAMPLE_SERP = """
<html><body>
<a href="/url?q=https%3A%2F%2Fexample.com%2Fresult&amp;sa=U">Result</a>
<a href="https://www.google.com/search">skip</a>
</body></html>
"""


@pytest.fixture(autouse=True)
def _reset_session() -> None:
    get_browser_session().reset()


@pytest.fixture
def session() -> BrowserSession:
    return get_browser_session()


# ---------------------------------------------------------------------------
# BrowserSession
# ---------------------------------------------------------------------------


def test_session_navigate_updates_state(session: BrowserSession) -> None:
    session.navigate("https://example.com")
    assert session.current_url == "https://example.com"
    assert session.tabs[0] == "https://example.com"


def test_session_go_back_and_forward(session: BrowserSession) -> None:
    session.navigate("https://a.com")
    session.navigate("https://b.com")
    assert session.go_back() == "https://a.com"
    assert session.go_forward() == "https://b.com"


def test_session_go_back_empty_returns_none(session: BrowserSession) -> None:
    assert session.go_back() is None


def test_session_open_and_close_tabs(session: BrowserSession) -> None:
    session.navigate("https://a.com")
    idx = session.open_new_tab("https://b.com")
    assert idx == 1
    assert session.current_url == "https://b.com"
    session.close_current_tab()
    assert session.current_url == "https://a.com"


def test_session_extract_title_and_text(session: BrowserSession) -> None:
    assert session.get_page_title(SAMPLE_HTML) == "Test Page"
    text = session.get_page_text(SAMPLE_HTML)
    assert "Hello world from Jarvis" in text
    assert "ignore me" not in text


def test_session_summarize_truncates(session: BrowserSession) -> None:
    long_html = f"<html><body><p>{'word ' * 500}</p></body></html>"
    summary = session.summarize(long_html, max_chars=50)
    assert len(summary) <= 51  # includes ellipsis
    assert summary.endswith("…")


def test_session_extract_first_result_url(session: BrowserSession) -> None:
    url = session.extract_first_result_url(SAMPLE_SERP)
    assert url == "https://example.com/result"


def test_session_snapshot(session: BrowserSession) -> None:
    session.navigate("https://example.com")
    snap = session.snapshot()
    assert snap["current_url"] == "https://example.com"
    assert snap["tab_count"] == 1


# ---------------------------------------------------------------------------
# Action handlers
# ---------------------------------------------------------------------------


@patch("webbrowser.open")
def test_handle_search_google(mock_open: Any, session: BrowserSession) -> None:
    mock_open.return_value = True
    registry = get_action_registry()
    result = registry.dispatch("search_google", session, query="Python tutorials")

    assert isinstance(result, BrowserActionResult)
    assert result.status == "success"
    assert result.data["query"] == "Python tutorials"
    assert "google.com/search" in result.data["url"]
    mock_open.assert_called_once()


def test_handle_search_google_empty_query(session: BrowserSession) -> None:
    result = get_action_registry().dispatch("search_google", session, query="  ")
    assert result is not None
    assert result.status == "error"
    assert "empty" in result.message.lower()


@patch("webbrowser.open")
def test_handle_open_first_result(mock_open: Any, session: BrowserSession) -> None:
    mock_open.return_value = True
    session.navigate("https://www.google.com/search?q=test")

    with patch.object(session, "fetch_page", return_value=SAMPLE_SERP):
        result = get_action_registry().dispatch("open_first_result", session)

    assert result is not None
    assert result.status == "success"
    assert result.data["url"] == "https://example.com/result"
    assert session.current_url == "https://example.com/result"


def test_handle_open_first_result_no_page(session: BrowserSession) -> None:
    result = get_action_registry().dispatch("open_first_result", session)
    assert result is not None
    assert result.status == "error"


@patch("webbrowser.open_new_tab")
def test_handle_open_new_tab(mock_new_tab: Any, session: BrowserSession) -> None:
    mock_new_tab.return_value = True
    result = get_action_registry().dispatch(
        "open_new_tab", session, url="https://example.com"
    )

    assert result is not None
    assert result.status == "success"
    assert result.data["url"] == "https://example.com"
    assert session.current_url == "https://example.com"


def test_handle_close_tab(session: BrowserSession) -> None:
    session.navigate("https://a.com")
    session.open_new_tab("https://b.com")
    result = get_action_registry().dispatch("close_tab", session)

    assert result is not None
    assert result.status == "success"
    assert session.current_url == "https://a.com"


@patch("webbrowser.open")
def test_handle_refresh(mock_open: Any, session: BrowserSession) -> None:
    mock_open.return_value = True
    session.navigate("https://example.com")
    result = get_action_registry().dispatch("refresh", session)

    assert result is not None
    assert result.status == "success"
    mock_open.assert_called_with("https://example.com")


@patch("webbrowser.open")
def test_handle_go_back(mock_open: Any, session: BrowserSession) -> None:
    mock_open.return_value = True
    session.navigate("https://a.com")
    session.navigate("https://b.com")
    result = get_action_registry().dispatch("go_back", session)

    assert result is not None
    assert result.status == "success"
    assert result.data["url"] == "https://a.com"


@patch("webbrowser.open")
def test_handle_go_forward(mock_open: Any, session: BrowserSession) -> None:
    mock_open.return_value = True
    session.navigate("https://a.com")
    session.navigate("https://b.com")
    session.go_back()
    result = get_action_registry().dispatch("go_forward", session)

    assert result is not None
    assert result.status == "success"
    assert result.data["url"] == "https://b.com"


def test_handle_read_page(session: BrowserSession) -> None:
    session.navigate("https://example.com")
    with patch.object(session, "fetch_page", return_value=SAMPLE_HTML):
        result = get_action_registry().dispatch("read_page", session)

    assert result is not None
    assert result.status == "success"
    assert result.data["title"] == "Test Page"
    assert "Hello world" in result.data["text"]


def test_handle_get_page_title(session: BrowserSession) -> None:
    session.navigate("https://example.com")
    with patch.object(session, "fetch_page", return_value=SAMPLE_HTML):
        result = get_action_registry().dispatch("get_page_title", session)

    assert result is not None
    assert result.status == "success"
    assert result.data["title"] == "Test Page"


def test_handle_get_page_text(session: BrowserSession) -> None:
    session.navigate("https://example.com")
    with patch.object(session, "fetch_page", return_value=SAMPLE_HTML):
        result = get_action_registry().dispatch("get_page_text", session)

    assert result is not None
    assert result.status == "success"
    assert "Hello world" in result.data["text"]


def test_handle_summarize_page(session: BrowserSession) -> None:
    session.navigate("https://example.com")
    with patch.object(session, "fetch_page", return_value=SAMPLE_HTML):
        result = get_action_registry().dispatch("summarize_page", session)

    assert result is not None
    assert result.status == "success"
    assert "Hello world" in result.data["summary"]


def test_handle_page_reader_no_url(session: BrowserSession) -> None:
    result = get_action_registry().dispatch("read_page", session)
    assert result is not None
    assert result.status == "error"


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------


def test_registry_lists_all_actions() -> None:
    actions = get_action_registry().list_actions()
    expected = {
        "search_google",
        "open_first_result",
        "open_new_tab",
        "close_tab",
        "refresh",
        "go_back",
        "go_forward",
        "read_page",
        "get_page_title",
        "get_page_text",
        "summarize_page",
    }
    assert expected.issubset(set(actions))


def test_registry_unknown_action_returns_none(session: BrowserSession) -> None:
    assert get_action_registry().dispatch("nonexistent", session) is None


# ---------------------------------------------------------------------------
# BrowserTool automation tier
# ---------------------------------------------------------------------------


@patch("webbrowser.open")
def test_browser_tool_execute_search_google(mock_open: Any) -> None:
    mock_open.return_value = True
    tool = BrowserTool()
    result = tool.execute(action="search_google", query="AI news")

    assert isinstance(result, BrowserActionResult)
    assert result.status == "success"
    assert result.data["query"] == "AI news"


@patch.object(BrowserSession, "fetch_page", return_value=SAMPLE_HTML)
def test_browser_tool_execute_read_page(_mock_fetch: MagicMock) -> None:
    tool = BrowserTool()
    tool.get_session().navigate("https://example.com")
    result = tool.execute(action="read_page")

    assert isinstance(result, BrowserActionResult)
    assert result.status == "success"


def test_browser_action_result_to_dict() -> None:
    result = BrowserActionResult.success("test", "ok", 0.1, data={"key": "val"})
    d = result.to_dict()
    assert d["action"] == "test"
    assert d["status"] == "success"
    assert d["data"] == {"key": "val"}
