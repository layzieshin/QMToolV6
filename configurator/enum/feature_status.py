"""
FeatureStatus - Status eines Features in der Registry.

Author: QMToolV6 Development Team
Version: 1.0.0
"""
from __future__ import annotations

from enum import Enum


class FeatureStatus(str, Enum):
    """
    Status eines Features in der Registry.

    MVP: Alle Features haben ACTIVE (keine Deaktivierung).
    Zukünftig:  DISABLED (deaktiviert), LOADING (wird geladen), ERROR (Ladefehler).

    Values:
        ACTIVE: Feature ist verfügbar und kann genutzt werden
        DISABLED:  Feature ist deaktiviert (zukünftig)
        LOADING: Feature wird gerade geladen (zukünftig)
        ERROR: Feature konnte nicht geladen werden (zukünftig)
    """

    ACTIVE = "ACTIVE"
    """Feature ist verfügbar und einsatzbereit."""

    # Zukünftige Stati (auskommentiert für MVP)
    # DISABLED = "DISABLED"
    # LOADING = "LOADING"
    # ERROR = "ERROR"