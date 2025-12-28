"""
Enumerations für UserManagement Feature.

Definiert System-Rollen und User-Status für die Benutzerverwaltung.
"""

from enum import Enum


class SystemRole(str, Enum):
    """
    System-weite Rollen für Benutzer.

    Diese Rollen sind hart codiert und definieren grundlegende Berechtigungen:
    - ADMIN: Volle Kontrolle über das System
    - USER: Standard-Benutzer mit eingeschränkten Rechten
    - QMB: Qualitätsmanagement-Beauftragte/r mit speziellen QM-Rechten
    """
    ADMIN = "ADMIN"
    USER = "USER"
    QMB = "QMB"


class UserStatus(str, Enum):
    """
    Status eines Benutzers im System.

    - ACTIVE: Benutzer ist aktiv und kann sich anmelden
    - INACTIVE: Benutzer wurde deaktiviert (Soft-Delete)
    - LOCKED: Benutzer wurde nach fehlgeschlagenen Login-Versuchen gesperrt
    """
    ACTIVE = "active"
    INACTIVE = "inactive"
    LOCKED = "locked"
