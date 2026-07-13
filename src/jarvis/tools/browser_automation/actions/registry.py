"""Action registry for browser automation.

Maps action name strings to handler callables.  The registry is the *only*
place that needs to change when adding a new browser action.

Handler signature::

    handler(session: BrowserSession, **kwargs) -> BrowserActionResult

Usage::

    from jarvis.tools.browser_automation.actions.registry import get_action_registry
    registry = get_action_registry()
    handler = registry.get("search_google")
    result = handler(session, query="Python tutorials")
"""

from __future__ import annotations

from typing import Any, Callable

from jarvis.tools.browser_automation.result import BrowserActionResult
from jarvis.tools.browser_automation.state import BrowserSession

# Import all handler modules
from jarvis.tools.browser_automation.actions.navigation import (
    handle_close_tab,
    handle_go_back,
    handle_go_forward,
    handle_open_first_result,
    handle_open_new_tab,
    handle_refresh,
    handle_search_google,
)
from jarvis.tools.browser_automation.actions.page_reader import (
    handle_get_page_text,
    handle_get_page_title,
    handle_read_page,
    handle_summarize_page,
)

# Type alias
ActionHandler = Callable[..., BrowserActionResult]

# ---------------------------------------------------------------------------
# Central mapping  →  action name : handler function
# To add a new action: import your handler and add one line here.
# ---------------------------------------------------------------------------
_ACTION_MAP: dict[str, ActionHandler] = {
    # Navigation
    "search_google": handle_search_google,
    "open_first_result": handle_open_first_result,
    "open_new_tab": handle_open_new_tab,
    "close_tab": handle_close_tab,
    "refresh": handle_refresh,
    "go_back": handle_go_back,
    "go_forward": handle_go_forward,
    # Page reading
    "read_page": handle_read_page,
    "get_page_title": handle_get_page_title,
    "get_page_text": handle_get_page_text,
    "summarize_page": handle_summarize_page,
}


class ActionRegistry:
    """Immutable lookup table from action-name → handler callable."""

    def __init__(self, mapping: dict[str, ActionHandler]) -> None:
        self._map: dict[str, ActionHandler] = dict(mapping)

    def get(self, action: str) -> ActionHandler | None:
        """Return the handler for *action*, or ``None`` if not registered."""
        return self._map.get(action)

    def dispatch(
        self,
        action: str,
        session: BrowserSession,
        **kwargs: Any,
    ) -> BrowserActionResult | None:
        """Dispatch *action* to its handler.

        Returns ``None`` if the action is not registered so the caller
        (BrowserTool) can fall through to its own logic.
        """
        handler = self.get(action)
        if handler is None:
            return None
        return handler(session, **kwargs)

    def list_actions(self) -> list[str]:
        """Return all registered action names (sorted)."""
        return sorted(self._map.keys())


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------
_registry: ActionRegistry | None = None


def get_action_registry() -> ActionRegistry:
    """Return the process-level :class:`ActionRegistry` singleton."""
    global _registry
    if _registry is None:
        _registry = ActionRegistry(_ACTION_MAP)
    return _registry
