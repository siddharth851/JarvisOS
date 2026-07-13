"""Browser tool implementation."""

from typing import Any
import webbrowser

from jarvis.tools.base import BaseTool
from jarvis.tools.exceptions import ToolError


class BrowserTool(BaseTool):
    """Tool for performing browser-related actions like opening URLs."""

    @property
    def name(self) -> str:
        """The unique name identifier of the tool."""
        return "browser_tool"

    @property
    def description(self) -> str:
        """A brief description explaining what the tool does and its purpose."""
        return (
            "A tool to open URLs, resolve website destinations from natural "
            "language, and search Google using the web browser."
        )

    # ------------------------------------------------------------------
    # Core primitives (unchanged public API)
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

        # Basic validation to ensure it starts with http:// or https://
        if not (url.startswith("http://") or url.startswith("https://")):
            raise ToolError(f"Invalid URL: '{url}'. Must start with 'http://' or 'https://'")

        try:
            return webbrowser.open(url)
        except Exception as e:
            raise ToolError(f"Failed to open URL '{url}': {e}")

    def open_google(self) -> bool:
        """Open google.com in the default web browser.

        Returns:
            True if browser open was triggered successfully.
        """
        return self.open_url("https://google.com")

    # ------------------------------------------------------------------
    # Extended capability: generic destination + Google search
    # ------------------------------------------------------------------

    def open_destination(self, destination: str) -> bool:
        """Resolve *destination* and open it in the default web browser.

        The resolution logic lives entirely in :class:`URLResolver` and
        follows this priority:

        1. Full URL (``http://`` / ``https://`` prefix)
        2. Bare domain (e.g. ``github.com``)
        3. Known website name (e.g. "GitHub", "ChatGPT", "Canva")
        4. Google search fallback

        Args:
            destination: Raw destination string from user input.

        Returns:
            True if browser open was triggered successfully.

        Raises:
            ToolError: If *destination* is empty or the browser fails.
        """
        if not destination or not destination.strip():
            raise ToolError("destination cannot be empty")

        from jarvis.services.url_resolver import get_url_resolver

        try:
            resolver = get_url_resolver()
            url = resolver.resolve(destination)
        except ValueError as e:
            raise ToolError(str(e))

        return self.open_url(url)

    def open_google_search(self, query: str) -> bool:
        """Perform a Google search for *query* in the default web browser.

        Args:
            query: The search query string.

        Returns:
            True if browser open was triggered successfully.

        Raises:
            ToolError: If *query* is empty or the browser fails.
        """
        if not query or not query.strip():
            raise ToolError("query cannot be empty")

        from urllib.parse import quote_plus

        url = f"https://www.google.com/search?q={quote_plus(query.strip())}"
        return self.open_url(url)

    # ------------------------------------------------------------------
    # execute() dispatcher — backward compatible
    # ------------------------------------------------------------------

    def execute(self, **kwargs: Any) -> Any:
        """Execute the browser tool action.

        Args:
            action: The action to perform.
                    Supported values:
                    - ``"open_url"``          — open a raw http(s) URL
                    - ``"open_google"``        — open google.com
                    - ``"open_destination"``   — resolve destination & open
                    - ``"open_google_search"`` — Google search for a query
            url: The URL to open (required for ``"open_url"``).
            destination: Destination string (required for ``"open_destination"``).
            query: Search query (required for ``"open_google_search"``).

        Returns:
            True if browser open was triggered successfully.

        Raises:
            ToolError: If action is missing, unsupported, or parameters are invalid.
        """
        action = kwargs.get("action")
        if not action:
            raise ToolError("Missing 'action' parameter for browser_tool")

        if action == "open_url":
            url = kwargs.get("url")
            if url is None:
                raise ToolError("Missing 'url' parameter for 'open_url' action")
            return self.open_url(url)

        elif action == "open_google":
            return self.open_google()

        elif action == "open_destination":
            destination = kwargs.get("destination")
            if destination is None:
                raise ToolError("Missing 'destination' parameter for 'open_destination' action")
            return self.open_destination(destination)

        elif action == "open_google_search":
            query = kwargs.get("query")
            if query is None:
                raise ToolError("Missing 'query' parameter for 'open_google_search' action")
            return self.open_google_search(query)

        else:
            raise ToolError(f"Unsupported action: '{action}'")
