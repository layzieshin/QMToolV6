"""
ConfigValidationException - App-Config ist ungültig.

Author: QMToolV6 Development Team
Version: 1.0.0
"""
from __future__ import annotations


class ConfigValidationException(Exception):
    """
    config/app_config.json ist ungültig.

    Wird geworfen wenn:
    - JSON ist nicht parsebar
    - Werte außerhalb gültiger Bereiche (z.B. timeout <= 0)
    - Erforderliche Sections fehlen
    - Pfade nicht existieren/nicht lesbar sind

    Unterschied zu InvalidMetaException:
    - InvalidMetaException: Feature-spezifische meta.json
    - ConfigValidationException:  Globale app_config.json

    Attributes:
        field: Name des ungültigen Feldes (optional)
        value: Ungültiger Wert (optional)
        reason: Beschreibung des Fehlers

    Example:
        >>> raise ConfigValidationException(
        ...     "session. timeout_minutes",
        ...     -1,
        ...     "Muss > 0 sein"
        ...  )
    """

    def __init__(
            self,
            field: str,
            value: any = None,
            reason: str = ""
    ):
        """
        Initialisiert Exception.

        Args:
            field: Name des ungültigen Config-Feldes
            value:  Der ungültige Wert (optional)
            reason: Beschreibung warum ungültig
        """
        message = f"Ungültige App-Konfiguration in '{field}'"
        if value is not None:
            message += f" (Wert: {value})"
        if reason:
            message += f":  {reason}"

        super().__init__(message)
        self.field = field
        self.value = value
        self.reason = reason