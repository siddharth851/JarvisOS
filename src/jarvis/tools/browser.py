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
        return "A tool to open URLs and search Google using the web browser."

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

    def execute(self, **kwargs: Any) -> Any:
        """Execute the browser tool action.

        Args:
            action: The action to perform ("open_url" or "open_google").
            url: The URL to open (required for "open_url").

        Returns:
            True if browser open was triggered successfully.

        Raises:
            ToolError: If action is missing, unsupported, or if parameters are invalid.
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

        else:
            raise ToolError(f"Unsupported action: '{action}'")
