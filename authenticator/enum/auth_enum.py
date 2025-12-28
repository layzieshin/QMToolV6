"""Enumerations für Authenticator."""
from enum import Enum


class SessionStatus(Enum):
    """Status einer Session."""
    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"
    INVALID = "INVALID"
