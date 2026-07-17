"""Application Manager.

Provides actions to launch, close, focus and detect running state for
applications. Uses subprocess-based commands so calls can be mocked in tests.
"""
from __future__ import annotations

import shlex
import subprocess
import time
from typing import Optional


def _now() -> float:
    return time.time()


def _wrap_response(action: str, target: str, status: str, message: str, start: float, data: Optional[dict] = None) -> dict:
    return {
        "action": action,
        "target": target,
        "status": status,
        "message": message,
        "execution_time": round(time.time() - start, 4),
        "data": data or {},
    }


class ApplicationManager:
    """Manager that performs application lifecycle actions.

    NOTE: Implementation prefers macOS-friendly commands like `open` and
    `osascript` where appropriate but falls back to generic process
    operations using `pkill`/`pgrep` so it remains cross-platform to an
    extent. All external calls use `subprocess` to allow tests to mock them.
    """

    def launch(self, identifier: str) -> dict:
        """Launch an application by path or identifier.

        If the identifier is a path to an `.app` bundle, use `open` on macOS.
        Otherwise, call the identifier as an executable.
        """
        start = _now()
        try:
            if identifier.endswith(".app"):
                # open application bundle
                cmd = ["open", identifier]
                subprocess.run(cmd, check=True)
            else:
                # attempt to launch executable path
                cmd = shlex.split(identifier) if " " in identifier else [identifier]
                subprocess.Popen(cmd)

            return _wrap_response("launch", identifier, "success", "launched", start, {"cmd": cmd})
        except Exception as exc:  # pragma: no cover - bubble to tests
            return _wrap_response("launch", identifier, "failure", str(exc), start)

    def close(self, identifier: str) -> dict:
        """Attempt to close/terminate an application.

        Tries an orderly quit via `osascript` on macOS, then falls back to
        `pkill -f` to ensure the process is terminated.
        """
        start = _now()
        try:
            # try osascript quit (macOS)
            try:
                app_name = identifier.split("/")[-1]
                if app_name.endswith(".app"):
                    app_name = app_name[:-4]
                cmd = ["osascript", "-e", f'tell application \"{app_name}\" to quit' ]
                subprocess.run(cmd, check=True)
                return _wrap_response("close", identifier, "success", "closed", start, {"cmd": cmd})
            except Exception:
                # fallback to pkill
                cmd = ["pkill", "-f", identifier]
                subprocess.run(cmd, check=True)
                return _wrap_response("close", identifier, "success", "killed", start, {"cmd": cmd})
        except Exception as exc:
            return _wrap_response("close", identifier, "failure", str(exc), start)

    def focus(self, identifier: str) -> dict:
        """Bring an application to the foreground.

        On macOS uses `osascript` activate; otherwise returns failure if not available.
        """
        start = _now()
        try:
            app_name = identifier.split("/")[-1]
            if app_name.endswith(".app"):
                app_name = app_name[:-4]
            cmd = ["osascript", "-e", f'tell application \"{app_name}\" to activate' ]
            subprocess.run(cmd, check=True)
            return _wrap_response("focus", identifier, "success", "focused", start, {"cmd": cmd})
        except Exception as exc:
            return _wrap_response("focus", identifier, "failure", str(exc), start)

    def is_running(self, identifier: str) -> bool:
        """Return True if a process matching *identifier* is running.

        Uses `pgrep -f` as a lightweight check; returns False on errors.
        """
        try:
            cmd = ["pgrep", "-f", identifier]
            res = subprocess.run(cmd, check=False, capture_output=True)
            return res.returncode == 0
        except Exception:
            return False


# Module-level instance convenience
_default_manager: Optional[ApplicationManager] = None


def get_application_manager() -> ApplicationManager:
    global _default_manager
    if _default_manager is None:
        _default_manager = ApplicationManager()
    return _default_manager
