"""Page reading action handlers.

Covers:
- read_page       — fetch and return full visible text
- get_page_title  — extract page <title>
- get_page_text   — extract visible body text
- summarize_page  — return a condensed excerpt
"""

from __future__ import annotations

import time

from jarvis.tools.browser_automation.result import BrowserActionResult
from jarvis.tools.browser_automation.state import BrowserSession


def handle_read_page(session: BrowserSession, **kwargs) -> BrowserActionResult:
    """Fetch the current page and return its full visible text.

    Optional kwargs
    ---------------
    url : str  — fetch this URL instead of the current one
    """
    t0 = time.perf_counter()
    action = "read_page"

    target_url: str | None = (kwargs.get("url") or "").strip() or session.current_url
    if not target_url:
        return BrowserActionResult.error(
            action,
            "No page to read. Open a URL first.",
            time.perf_counter() - t0,
        )

    raw_html = session.fetch_page(target_url)
    if not raw_html:
        return BrowserActionResult.error(
            action,
            f"Could not fetch page: {target_url}",
            time.perf_counter() - t0,
        )

    title = session.get_page_title(raw_html)
    text = session.get_page_text(raw_html)
    return BrowserActionResult.success(
        action,
        f"Read page: {title or target_url}",
        time.perf_counter() - t0,
        data={
            "url": target_url,
            "title": title,
            "text": text,
            "char_count": len(text),
        },
    )


def handle_get_page_title(session: BrowserSession, **kwargs) -> BrowserActionResult:
    """Fetch the current page and return its <title> element text.

    Optional kwargs
    ---------------
    url : str  — fetch this URL instead of the current one
    """
    t0 = time.perf_counter()
    action = "get_page_title"

    target_url: str | None = (kwargs.get("url") or "").strip() or session.current_url
    if not target_url:
        return BrowserActionResult.error(
            action,
            "No page to inspect. Open a URL first.",
            time.perf_counter() - t0,
        )

    raw_html = session.fetch_page(target_url)
    if not raw_html:
        return BrowserActionResult.error(
            action,
            f"Could not fetch page: {target_url}",
            time.perf_counter() - t0,
        )

    title = session.get_page_title(raw_html)
    return BrowserActionResult.success(
        action,
        f"Page title: {title!r}" if title else "No <title> found",
        time.perf_counter() - t0,
        data={"url": target_url, "title": title},
    )


def handle_get_page_text(session: BrowserSession, **kwargs) -> BrowserActionResult:
    """Fetch the current page and return its visible body text.

    Optional kwargs
    ---------------
    url : str  — fetch this URL instead of the current one
    """
    t0 = time.perf_counter()
    action = "get_page_text"

    target_url: str | None = (kwargs.get("url") or "").strip() or session.current_url
    if not target_url:
        return BrowserActionResult.error(
            action,
            "No page to read. Open a URL first.",
            time.perf_counter() - t0,
        )

    raw_html = session.fetch_page(target_url)
    if not raw_html:
        return BrowserActionResult.error(
            action,
            f"Could not fetch page: {target_url}",
            time.perf_counter() - t0,
        )

    text = session.get_page_text(raw_html)
    return BrowserActionResult.success(
        action,
        f"Extracted {len(text)} characters of text",
        time.perf_counter() - t0,
        data={"url": target_url, "text": text, "char_count": len(text)},
    )


def handle_summarize_page(session: BrowserSession, **kwargs) -> BrowserActionResult:
    """Fetch the current page and return a condensed plain-text summary.

    Optional kwargs
    ---------------
    url       : str  — fetch this URL instead of the current one
    max_chars : int  — maximum characters in the summary (default 1500)
    """
    t0 = time.perf_counter()
    action = "summarize_page"

    target_url: str | None = (kwargs.get("url") or "").strip() or session.current_url
    max_chars: int = int(kwargs.get("max_chars") or 1500)

    if not target_url:
        return BrowserActionResult.error(
            action,
            "No page to summarize. Open a URL first.",
            time.perf_counter() - t0,
        )

    raw_html = session.fetch_page(target_url)
    if not raw_html:
        return BrowserActionResult.error(
            action,
            f"Could not fetch page: {target_url}",
            time.perf_counter() - t0,
        )

    title = session.get_page_title(raw_html)
    summary = session.summarize(raw_html, max_chars=max_chars)
    return BrowserActionResult.success(
        action,
        f"Summarized: {title or target_url}",
        time.perf_counter() - t0,
        data={
            "url": target_url,
            "title": title,
            "summary": summary,
            "char_count": len(summary),
        },
    )
