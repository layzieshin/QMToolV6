"""Enums for UI feature."""
from enum import Enum


class UIAction(str, Enum):
    """Actions tracked by UI events."""

    LOGIN = "login"
    LOGOUT = "logout"
    REGISTER = "register"
    VIEW_LOGS = "view_logs"
