"""Structured result returned by every browser automation action."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class BrowserActionResult:
    """Uniform response envelope for every browser automation action.

    Every handler must populate ``action``, ``status``, ``message`` and
    ``execution_time``.  The ``data`` field carries action-specific payload
    (e.g. extracted text, page title) and may be ``None`` when there is
    nothing extra to return.

    Fields
    ------
    action : str
        The action name that was executed (e.g. ``"search_google"``).
    status : str
        ``"success"`` or ``"error"``.
    message : str
        Human-readable summary of what happened.
    execution_time : float
        Wall-clock seconds taken by the action.
    data : Any
        Optional action-specific payload (dict, str, list, …).
    """

    action: str
    status: str
    message: str
    execution_time: float
    data: Any = field(default=None)

    # ------------------------------------------------------------------
    # Convenience constructors
    # ------------------------------------------------------------------

    @classmethod
    def success(
        cls,
        action: str,
        message: str,
        execution_time: float,
        data: Any = None,
    ) -> "BrowserActionResult":
        """Return a successful result."""
        return cls(
            action=action,
            status="success",
            message=message,
            execution_time=execution_time,
            data=data,
        )

    @classmethod
    def error(
        cls,
        action: str,
        message: str,
        execution_time: float,
        data: Any = None,
    ) -> "BrowserActionResult":
        """Return an error result."""
        return cls(
            action=action,
            status="error",
            message=message,
            execution_time=execution_time,
            data=data,
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialise to a plain dictionary."""
        return {
            "action": self.action,
            "status": self.status,
            "message": self.message,
            "execution_time": self.execution_time,
            "data": self.data,
        }
