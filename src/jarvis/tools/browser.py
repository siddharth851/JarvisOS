"""Browser tool implementation.

Preserves the complete existing public API (open_url, open_google,
open_destination, open_google_search, execute()) and adds a new
automation layer that delegates to the modular
:class:`~jarvis.tools.browser_automation.actions.registry.ActionRegistry`.

New automation actions are dispatched via ``execute(action=<name>, ...)``
and always return a :class:`~jarvis.tools.browser_automation.result.BrowserActionResult`.
Legacy actions (``open_url``, ``open_google``, ``open_destination``,
``open_google_search``) continue to return ``bool`` as before.
"""

from typing import Any
import webbrowser

from jarvis.tools.base import BaseTool
from jarvis.tools.exceptions import ToolError


class BrowserTool(BaseTool):
    """Tool for performing browser-related actions.

    Supports two tiers of capability:

    **Legacy tier** (returns ``bool``)
      - ``open_url``          — open a raw http(s) URL
      - ``open_google``       — open google.com
      - ``open_destination``  — resolve destination via URLResolver & open
      - ``open_google_search`` — Google search query

    **Automation tier** (returns :class:`BrowserActionResult`)
      - ``search_google``     — search & update session state
      - ``open_first_result`` — open first SERP result
      - ``open_new_tab``      — open a new browser tab
      - ``close_tab``         — close the active tab
      - ``refresh``           — reload current page
      - ``go_back``           — navigate back in history
      - ``go_forward``        — navigate forward
      - ``read_page``         — fetch & return full page text
      - ``get_page_title``    — extract page title
      - ``get_page_text``     — extract visible body text
      - ``summarize_page``    — return condensed excerpt
    """

    # ------------------------------------------------------------------
    # BaseTool interface
    # ------------------------------------------------------------------

    @property
    def name(self) -> str:
        """The unique name identifier of the tool."""
        return "browser_tool"

    @property
    def description(self) -> str:
        """A brief description explaining what the tool does and its purpose."""
        return (
            "A tool to open URLs, resolve website destinations from natural "
            "language, search Google, and automate browser reading actions."
        )

    # ------------------------------------------------------------------
    # Legacy primitives (unchanged public API — return bool)
    # ------------------------------------------------------------------

    def open_url(self, url: str) -> bool:
        """Open the specified URL in the default web browser.

        Args:
            url: The HTTP/HTTPS URL to open.

        Returns:
            True if browser open was triggered successfully.

        Raises:
            ToolError: If the URL is empty or invalid.
        """
        if not url:
            raise ToolError("URL cannot be empty")

        if not (url.startswith("http://") or url.startswith("https://")):
            raise ToolError(f"Invalid URL: '{url}'. Must start with 'http://' or 'https://'")

        try:
            return webbrowser.open(url)
        except Exception as e:
            raise ToolError(f"Failed to open URL '{url}': {e}")

    def open_google(self) -> bool:
        """Open google.com in the default web browser."""
        return self.open_url("https://google.com")

    def open_destination(self, destination: str) -> bool:
        """Resolve *destination* and open it in the default web browser.

        Resolution priority (handled by URLResolver):
        1. Full URL  2. Bare domain  3. Known site name  4. Google search

        Raises:
            ToolError: If *destination* is empty or the browser fails.
        """
        if not destination or not destination.strip():
            raise ToolError("destination cannot be empty")

        from jarvis.services.url_resolver import get_url_resolver

        try:
            url = get_url_resolver().resolve(destination)
        except ValueError as e:
            raise ToolError(str(e))

        return self.open_url(url)

    def open_google_search(self, query: str) -> bool:
        """Perform a Google search for *query* in the default web browser.

        Raises:
            ToolError: If *query* is empty or the browser fails.
        """
        if not query or not query.strip():
            raise ToolError("query cannot be empty")

        from urllib.parse import quote_plus

        url = f"https://www.google.com/search?q={quote_plus(query.strip())}"
        return self.open_url(url)

    # ------------------------------------------------------------------
    # Automation helpers (return BrowserActionResult)
    # ------------------------------------------------------------------

    def get_session(self):
        """Return the active :class:`BrowserSession` singleton."""
        from jarvis.tools.browser_automation.state import get_browser_session
        return get_browser_session()

    def _dispatch_automation(self, action: str, **kwargs: Any):
        """Dispatch *action* through the ActionRegistry.

        Returns a :class:`BrowserActionResult` or raises :class:`ToolError`
        if the action is not found in the registry.
        """
        from jarvis.tools.browser_automation.actions.registry import get_action_registry
        session = self.get_session()
        result = get_action_registry().dispatch(action, session, **kwargs)
        if result is None:
            raise ToolError(f"Unsupported action: '{action}'")
        return result

    # ------------------------------------------------------------------
    # execute() dispatcher — backward compatible
    # ------------------------------------------------------------------

    def execute(self, **kwargs: Any) -> Any:
        """Execute a browser action.

        For legacy actions the return type is ``bool``.
        For automation actions the return type is :class:`BrowserActionResult`.

        Args:
            action: Action name (see class docstring for full list).
            **kwargs: Action-specific parameters.

        Raises:
            ToolError: If action is missing, unsupported, or parameters invalid.
        """
        action = kwargs.get("action")
        if not action:
            raise ToolError("Missing 'action' parameter for browser_tool")

        # ---- Legacy tier (bool returns) ----
        if action == "open_url":
            url = kwargs.get("url")
            if url is None:
                raise ToolError("Missing 'url' parameter for 'open_url' action")
            return self.open_url(url)

        if action == "open_google":
            return self.open_google()

        if action == "open_destination":
            destination = kwargs.get("destination")
            if destination is None:
                raise ToolError("Missing 'destination' parameter for 'open_destination' action")
            return self.open_destination(destination)

        if action == "open_google_search":
            query = kwargs.get("query")
            if query is None:
                raise ToolError("Missing 'query' parameter for 'open_google_search' action")
            return self.open_google_search(query)

        # ---- Automation tier (BrowserActionResult returns) ----
        # Strip 'action' key so handlers only see their own kwargs
        handler_kwargs = {k: v for k, v in kwargs.items() if k != "action"}
        return self._dispatch_automation(action, **handler_kwargs)
