"""Navigation action handlers.

Covers:
- search_google
- open_first_result
- open_new_tab
- close_tab
- refresh
- go_back
- go_forward
"""

from __future__ import annotations

import time
import webbrowser
from urllib.parse import quote_plus

from jarvis.tools.browser_automation.result import BrowserActionResult
from jarvis.tools.browser_automation.state import BrowserSession


def handle_search_google(session: BrowserSession, **kwargs) -> BrowserActionResult:
    """Perform a Google search for *query* and update session state.

    Opens the search results page in the system browser.

    Required kwargs
    ---------------
    query : str  — the search query
    """
    t0 = time.perf_counter()
    action = "search_google"

    query: str = (kwargs.get("query") or "").strip()
    if not query:
        return BrowserActionResult.error(
            action, "query cannot be empty", time.perf_counter() - t0
        )

    url = f"https://www.google.com/search?q={quote_plus(query)}"
    try:
        webbrowser.open(url)
        session.navigate(url)
        return BrowserActionResult.success(
            action,
            f"Searching Google for: {query!r}",
            time.perf_counter() - t0,
            data={"query": query, "url": url},
        )
    except Exception as exc:
        return BrowserActionResult.error(
            action,
            f"Failed to open browser: {exc}",
            time.perf_counter() - t0,
        )


def handle_open_first_result(session: BrowserSession, **kwargs) -> BrowserActionResult:
    """Open the first organic search result from the current Google SERP.

    Fetches the current page (must be a Google search results page), extracts
    the first result URL, opens it and updates session state.
    """
    t0 = time.perf_counter()
    action = "open_first_result"

    if not session.current_url:
        return BrowserActionResult.error(
            action,
            "No active page. Run a Google search first.",
            time.perf_counter() - t0,
        )

    raw_html = session.fetch_page()
    if not raw_html:
        return BrowserActionResult.error(
            action,
            f"Could not fetch page: {session.current_url}",
            time.perf_counter() - t0,
        )

    result_url = session.extract_first_result_url(raw_html)
    if not result_url:
        return BrowserActionResult.error(
            action,
            "No result URL found on current page.",
            time.perf_counter() - t0,
        )

    try:
        webbrowser.open(result_url)
        session.navigate(result_url)
        return BrowserActionResult.success(
            action,
            f"Opened first result: {result_url}",
            time.perf_counter() - t0,
            data={"url": result_url},
        )
    except Exception as exc:
        return BrowserActionResult.error(
            action,
            f"Failed to open browser: {exc}",
            time.perf_counter() - t0,
        )


def handle_open_new_tab(session: BrowserSession, **kwargs) -> BrowserActionResult:
    """Open a new browser tab, optionally pre-navigated to *url*.

    Optional kwargs
    ---------------
    url : str  — if provided, open this URL in the new tab
    """
    t0 = time.perf_counter()
    action = "open_new_tab"

    url: str | None = (kwargs.get("url") or "").strip() or None

    try:
        if url:
            if not (url.startswith("http://") or url.startswith("https://")):
                url = f"https://{url}"
            webbrowser.open_new_tab(url)
        else:
            webbrowser.open_new_tab("about:blank")

        tab_index = session.open_new_tab(url)
        return BrowserActionResult.success(
            action,
            f"Opened new tab (index {tab_index})" + (f" at {url}" if url else ""),
            time.perf_counter() - t0,
            data={"tab_index": tab_index, "url": url},
        )
    except Exception as exc:
        return BrowserActionResult.error(
            action,
            f"Failed to open new tab: {exc}",
            time.perf_counter() - t0,
        )


def handle_close_tab(session: BrowserSession, **kwargs) -> BrowserActionResult:
    """Close the current tab and activate the nearest remaining one."""
    t0 = time.perf_counter()
    action = "close_tab"

    active_url = session.current_url
    remaining_url = session.close_current_tab()
    return BrowserActionResult.success(
        action,
        f"Closed tab ({active_url or 'blank'}). Now at: {remaining_url or 'blank'}",
        time.perf_counter() - t0,
        data={"closed_url": active_url, "now_active": remaining_url},
    )


def handle_refresh(session: BrowserSession, **kwargs) -> BrowserActionResult:
    """Reload the current page in the browser."""
    t0 = time.perf_counter()
    action = "refresh"

    if not session.current_url:
        return BrowserActionResult.error(
            action,
            "No active page to refresh.",
            time.perf_counter() - t0,
        )

    try:
        webbrowser.open(session.current_url)
        return BrowserActionResult.success(
            action,
            f"Refreshed: {session.current_url}",
            time.perf_counter() - t0,
            data={"url": session.current_url},
        )
    except Exception as exc:
        return BrowserActionResult.error(
            action,
            f"Failed to refresh: {exc}",
            time.perf_counter() - t0,
        )


def handle_go_back(session: BrowserSession, **kwargs) -> BrowserActionResult:
    """Navigate to the previous page in history."""
    t0 = time.perf_counter()
    action = "go_back"

    prev_url = session.go_back()
    if prev_url is None:
        return BrowserActionResult.error(
            action,
            "No previous page in history.",
            time.perf_counter() - t0,
        )

    try:
        webbrowser.open(prev_url)
        return BrowserActionResult.success(
            action,
            f"Navigated back to: {prev_url}",
            time.perf_counter() - t0,
            data={"url": prev_url},
        )
    except Exception as exc:
        return BrowserActionResult.error(
            action,
            f"Failed to navigate back: {exc}",
            time.perf_counter() - t0,
        )


def handle_go_forward(session: BrowserSession, **kwargs) -> BrowserActionResult:
    """Navigate to the next page in the forward stack."""
    t0 = time.perf_counter()
    action = "go_forward"

    next_url = session.go_forward()
    if next_url is None:
        return BrowserActionResult.error(
            action,
            "No forward page available.",
            time.perf_counter() - t0,
        )

    try:
        webbrowser.open(next_url)
        return BrowserActionResult.success(
            action,
            f"Navigated forward to: {next_url}",
            time.perf_counter() - t0,
            data={"url": next_url},
        )
    except Exception as exc:
        return BrowserActionResult.error(
            action,
            f"Failed to navigate forward: {exc}",
            time.perf_counter() - t0,
        )
