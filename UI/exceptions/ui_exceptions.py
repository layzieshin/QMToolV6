"""Custom exceptions for UI feature."""


class UIException(Exception):
    """Base exception for UI errors."""


class UIValidationError(UIException):
    """Raised when user input is invalid."""


class UIAuthenticationError(UIException):
    """Raised when authentication fails."""


class UIDataLoadError(UIException):
    """Raised when metadata cannot be loaded."""
