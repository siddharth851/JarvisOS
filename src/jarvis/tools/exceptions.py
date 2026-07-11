"""Custom exceptions for JarvisOS tools."""


class ToolError(Exception):
    """Base exception for all tool-related errors in JarvisOS."""


class ToolNotFoundError(ToolError):
    """Raised when a requested tool cannot be found."""


class ToolRegistrationError(ToolError):
    """Raised when tool registration fails, e.g. due to name duplication or invalid type."""
