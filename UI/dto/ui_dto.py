"""DTOs for the UI feature."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict


@dataclass(frozen=True)
class UILoginDTO:
    """Login request data."""

    username: str
    password: str


@dataclass(frozen=True)
class UIRegisterDTO:
    """Registration request data."""

    username: str
    password: str
    email: Optional[str] = None
    role: str = "USER"


@dataclass(frozen=True)
class CreateUIEventDTO:
    """DTO for creating a UI event."""

    username: str
    action: str
    details: Optional[Dict] = None


@dataclass(frozen=True)
class UIEventDTO:
    """DTO representing a stored UI event."""

    id: int
    timestamp: datetime
    username: str
    action: str
    details: Optional[Dict]
