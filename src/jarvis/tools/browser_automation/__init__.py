"""Browser Automation package.

Provides a modular, session-aware browser automation layer built entirely on
the Python standard library (``webbrowser``, ``urllib``, ``html.parser``).

Public surface
--------------
- :class:`BrowserSession`        — tracks current URL, history and tab list
- :class:`BrowserActionResult`   — structured response for every action
- :func:`get_browser_session`    — return the process-level singleton session
"""

from jarvis.tools.browser_automation.result import BrowserActionResult
from jarvis.tools.browser_automation.state import BrowserSession, get_browser_session

__all__ = [
    "BrowserActionResult",
    "BrowserSession",
    "get_browser_session",
]
