"""Data Transfer Objects für Authenticator."""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from ..enum.auth_enum import SessionStatus


@dataclass
class LoginRequestDTO:
    """DTO für Login-Anfrage."""
    username: str
    password: str


@dataclass
class SessionDTO:
    """DTO für Session-Informationen."""
    session_id: str
    user_id: int
    username: str
    created_at: datetime
    expires_at: datetime
    status: SessionStatus
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


@dataclass
class AuthenticationResultDTO:
    """DTO für Authentifizierungs-Ergebnis."""
    success: bool
    session: Optional[SessionDTO] = None
    error_message: Optional[str] = None
