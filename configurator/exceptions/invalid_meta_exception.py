"""
InvalidMetaException - meta.json ist ungültig.

Author: QMToolV6 Development Team
Version: 1.0.0
"""
from __future__ import annotations


class InvalidMetaException(Exception):
    """
    meta.json ist ungültig oder verletzt Konventionen.

    Wird geworfen wenn:
    - JSON ist nicht parsebar
    - Pflichtfelder fehlen (id, label, version, main_class)
    - id != Ordnername
    - Feldtypen stimmen nicht (z.B. visible_for ist kein Array)
    - Audit-Konfiguration ist ungültig

    Attributes:
        feature_id: ID/Ordnername des Features
        reason: Beschreibung des Fehlers

    Example:
        >>> raise InvalidMetaException("auth", "Pflichtfeld 'label' fehlt")
        InvalidMetaException:  Ungültige meta.json für Feature auth:  Pflichtfeld 'label' fehlt
    """

    def __init__(self, feature_id: str, reason: str):
        """
        Initialisiert Exception.

        Args:
            feature_id:  ID/Ordnername des Features
            reason: Beschreibung des Validierungsfehlers
        """
        super().__init__(f"Ungültige meta.json für Feature {feature_id}: {reason}")
        self.feature_id = feature_id
        self.reason = reason