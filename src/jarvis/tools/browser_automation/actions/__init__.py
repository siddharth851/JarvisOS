"""Browser action handlers package.

Each module in this package exports a single handler function that follows the
signature::

    handler(session: BrowserSession, **kwargs) -> BrowserActionResult

Handlers are registered in :mod:`jarvis.tools.browser_automation.actions.registry`
and dispatched by :class:`jarvis.tools.browser.BrowserTool`.

Adding a new action
-------------------
1. Create a new module (or add to an existing one) with a handler function.
2. Register it in ``registry.py`` — no other file needs changing.
"""
