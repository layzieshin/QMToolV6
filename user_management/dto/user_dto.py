"""
Data Transfer Objects für UserManagement Feature.

DTOs kapseln Daten für User-Operationen und vermeiden direkte Abhängigkeiten
zu internen Datenmodellen (z.B. ORM-Entities).
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from ..enum.user_enum import SystemRole, UserStatus


@dataclass
class UserDTO:
    """
    Vollständige Repräsentation eines Benutzers.

    Wird verwendet für Rückgabewerte von Service-Methoden.
    Passwort-Hash wird aus Sicherheitsgründen NICHT exponiert.
    """
    id: int
    username: str
    email: Optional[str]
    role: SystemRole
    status: UserStatus
    created_at: datetime
    last_login_at: Optional[datetime] = None


@dataclass
class CreateUserDTO:
    """
    Daten für die Erstellung eines neuen Benutzers.

    Passwort wird im Klartext übergeben, Service hasht es vor dem Speichern.
    """
    username: str
    password: str
    role: SystemRole
    email: Optional[str] = None


@dataclass
class UpdateUserDTO:
    """
    Daten für Profil-Updates eines Benutzers.

    Alle Felder sind optional - nur übergebene Werte werden aktualisiert.
    """
    email: Optional[str] = None
    # Weitere Profilfelder können hier ergänzt werden (z.B. display_name)
