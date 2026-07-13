"""Browser session state management.

:class:`BrowserSession` is an in-process, lightweight browser state machine.
It tracks the current URL, a linear back/forward history stack and a list of
open "tabs" (each tab is simply a URL string).

Because ``webbrowser.open`` / ``webbrowser.open_new_tab`` are fire-and-forget
(they hand off to the OS default browser), session state is maintained on the
Python side.  Page content fetching uses ``urllib`` from the standard library so
no additional dependencies are required.

Design rules
------------
- No global mutable state except through :func:`get_browser_session`.
- Session can be reset between tests via :meth:`BrowserSession.reset`.
- Fetching / parsing is *optional*: ``fetch_page`` gracefully degrades and
  returns ``None`` if the URL is unreachable.
"""

from __future__ import annotations

import html
import re
import time
import urllib.error
import urllib.request
from html.parser import HTMLParser
from typing import Optional


# ---------------------------------------------------------------------------
# Minimal HTML → text extractor (stdlib only)
# ---------------------------------------------------------------------------

class _TextExtractor(HTMLParser):
    """Feed HTML, collect visible text."""

    _SKIP_TAGS = frozenset(
        {"script", "style", "head", "meta", "link", "noscript", "svg", "path"}
    )

    def __init__(self) -> None:
        super().__init__()
        self._skip_depth = 0
        self._parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list) -> None:  # type: ignore[override]
        if tag.lower() in self._SKIP_TAGS:
            self._skip_depth += 1

    def handle_endtag(self, tag: str) -> None:  # type: ignore[override]
        if tag.lower() in self._SKIP_TAGS:
            self._skip_depth = max(0, self._skip_depth - 1)

    def handle_data(self, data: str) -> None:
        if self._skip_depth == 0:
            stripped = data.strip()
            if stripped:
                self._parts.append(html.unescape(stripped))

    def get_text(self) -> str:
        return " ".join(self._parts)


def _extract_title(raw_html: str) -> str:
    """Return the content of the first <title> tag, or empty string."""
    m = re.search(r"<title[^>]*>(.*?)</title>", raw_html, re.IGNORECASE | re.DOTALL)
    if m:
        return html.unescape(m.group(1).strip())
    return ""


def _extract_text(raw_html: str) -> str:
    """Return all visible text from an HTML document."""
    parser = _TextExtractor()
    try:
        parser.feed(raw_html)
    except Exception:
        pass
    return parser.get_text()


# ---------------------------------------------------------------------------
# BrowserSession
# ---------------------------------------------------------------------------

class BrowserSession:
    """Lightweight in-process browser state machine.

    Attributes tracked
    ------------------
    current_url : str | None
        The URL of the active tab (``None`` before any navigation).
    history : list[str]
        Visited URLs in chronological order (oldest first).
    forward_stack : list[str]
        URLs available for ``go_forward`` (cleared on new navigation).
    tabs : list[str | None]
        One entry per open tab (URL or ``None`` for blank tabs).
    active_tab_index : int
        Index into ``tabs`` of the currently active tab.
    """

    _FETCH_TIMEOUT = 10  # seconds

    def __init__(self) -> None:
        self.reset()

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def reset(self) -> None:
        """Reset session to initial blank state (useful between tests)."""
        self.current_url: Optional[str] = None
        self.history: list[str] = []
        self.forward_stack: list[str] = []
        self.tabs: list[Optional[str]] = [None]  # one blank tab
        self.active_tab_index: int = 0

    # ------------------------------------------------------------------
    # Navigation primitives
    # ------------------------------------------------------------------

    def navigate(self, url: str) -> None:
        """Record navigation to *url* and update history/tabs."""
        if self.current_url:
            self.history.append(self.current_url)
        self.forward_stack.clear()
        self.current_url = url
        self.tabs[self.active_tab_index] = url

    def go_back(self) -> Optional[str]:
        """Pop history stack; return previous URL or ``None`` if unavailable."""
        if not self.history:
            return None
        previous = self.history.pop()
        if self.current_url:
            self.forward_stack.append(self.current_url)
        self.current_url = previous
        self.tabs[self.active_tab_index] = previous
        return previous

    def go_forward(self) -> Optional[str]:
        """Pop forward stack; return next URL or ``None`` if unavailable."""
        if not self.forward_stack:
            return None
        next_url = self.forward_stack.pop()
        if self.current_url:
            self.history.append(self.current_url)
        self.current_url = next_url
        self.tabs[self.active_tab_index] = next_url
        return next_url

    # ------------------------------------------------------------------
    # Tab management
    # ------------------------------------------------------------------

    def open_new_tab(self, url: Optional[str] = None) -> int:
        """Append a new tab (optionally pre-navigated to *url*); activate it.

        Returns the index of the newly created tab.
        """
        self.tabs.append(url)
        self.active_tab_index = len(self.tabs) - 1
        if url:
            self.navigate(url)
        else:
            self.current_url = None
        return self.active_tab_index

    def close_current_tab(self) -> Optional[str]:
        """Close the active tab and activate the nearest remaining one.

        Returns the URL of the now-active tab, or ``None`` if no tabs remain.
        """
        if len(self.tabs) == 1:
            # Last tab: clear it but keep the slot
            closed_url = self.tabs[0]
            self.tabs[0] = None
            self.current_url = None
            self.history.clear()
            self.forward_stack.clear()
            return None

        self.tabs.pop(self.active_tab_index)
        self.active_tab_index = max(0, self.active_tab_index - 1)
        self.current_url = self.tabs[self.active_tab_index]
        return self.current_url

    # ------------------------------------------------------------------
    # Page fetching
    # ------------------------------------------------------------------

    def fetch_page(self, url: Optional[str] = None) -> Optional[str]:
        """Fetch raw HTML for *url* (defaults to current URL).

        Returns the raw HTML string or ``None`` on any network/parse failure.
        """
        target = url or self.current_url
        if not target:
            return None
        try:
            req = urllib.request.Request(
                target,
                headers={
                    "User-Agent": (
                        "Mozilla/5.0 (compatible; JarvisOS/1.0; +https://jarvis.ai)"
                    )
                },
            )
            with urllib.request.urlopen(req, timeout=self._FETCH_TIMEOUT) as resp:
                raw_bytes = resp.read(512 * 1024)  # cap at 512 KB
                charset = "utf-8"
                content_type = resp.headers.get("Content-Type", "")
                m = re.search(r"charset=([\w-]+)", content_type, re.IGNORECASE)
                if m:
                    charset = m.group(1)
                return raw_bytes.decode(charset, errors="replace")
        except Exception:
            return None

    # ------------------------------------------------------------------
    # Page reading helpers
    # ------------------------------------------------------------------

    def get_page_title(self, raw_html: str) -> str:
        """Extract title from already-fetched HTML."""
        return _extract_title(raw_html)

    def get_page_text(self, raw_html: str) -> str:
        """Extract visible text from already-fetched HTML."""
        return _extract_text(raw_html)

    def summarize(self, raw_html: str, max_chars: int = 1500) -> str:
        """Return a plain-text excerpt (first *max_chars* chars of body text)."""
        text = _extract_text(raw_html)
        # Collapse runs of whitespace
        text = re.sub(r"\s{2,}", " ", text).strip()
        if len(text) <= max_chars:
            return text
        # Cut at last space before the limit to avoid mid-word splits
        truncated = text[:max_chars]
        last_space = truncated.rfind(" ")
        if last_space > max_chars // 2:
            truncated = truncated[:last_space]
        return truncated + "…"

    # ------------------------------------------------------------------
    # Google search result extraction
    # ------------------------------------------------------------------

    @staticmethod
    def extract_first_result_url(raw_html: str) -> Optional[str]:
        """Parse a Google SERP HTML and return the first organic result URL.

        Google wraps result links in ``<a href="/url?q=<target>&…">`` anchors
        inside result divs.  We extract the *q=* parameter from the first
        matching anchor.
        """
        from urllib.parse import unquote

        # Google encodes result links as /url?q=<actual_url>&...
        pattern = re.compile(r'/url\?q=([^&"]+)', re.IGNORECASE)
        m = pattern.search(raw_html)
        if m:
            decoded = unquote(m.group(1))
            if decoded.startswith("http://") or decoded.startswith("https://"):
                return decoded
        # Fallback: look for direct <a href="https://..."> that are clearly result links
        pattern2 = re.compile(
            r'<a\s[^>]*href="(https?://(?!(?:www\.)?google\.[^/]+)[^"]+)"',
            re.IGNORECASE,
        )
        m2 = pattern2.search(raw_html)
        if m2:
            return m2.group(1)
        return None

    # ------------------------------------------------------------------
    # State snapshot
    # ------------------------------------------------------------------

    def snapshot(self) -> dict:
        """Return a serialisable snapshot of the current session state."""
        return {
            "current_url": self.current_url,
            "history": list(self.history),
            "forward_stack": list(self.forward_stack),
            "tabs": list(self.tabs),
            "active_tab_index": self.active_tab_index,
            "tab_count": len(self.tabs),
        }


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

_session: Optional[BrowserSession] = None


def get_browser_session() -> BrowserSession:
    """Return the process-level :class:`BrowserSession` singleton."""
    global _session
    if _session is None:
        _session = BrowserSession()
    return _session
