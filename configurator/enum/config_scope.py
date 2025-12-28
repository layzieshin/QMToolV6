"""
ConfigScope - Scope/Gültigkeitsbereich von Konfigurationen.

Author: QMToolV6 Development Team
Version: 1.0.0
"""
from __future__ import annotations

from enum import Enum


class ConfigScope(str, Enum):
    """
    Scope/Gültigkeitsbereich von Konfigurationen.

    Definiert, woher eine Konfiguration stammt und wer sie ändern darf.

    Future Use-Cases:
    - Config-Overrides (GLOBAL < FEATURE < USER)
    - Umgebungs-spezifische Configs (DEV vs PROD)
    - Permission-Checks (SYSTEM vs USER)

    Values:
        GLOBAL: Globale App-Konfiguration (config/app_config.json)
        FEATURE: Feature-spezifische Konfiguration (feature/meta.json)
        USER: User-spezifische Preferences (zukünftig)
        SYSTEM: System-Konfiguration (nur Admin)
    """

    GLOBAL = "GLOBAL"
    """Globale App-Konfiguration aus config/app_config.json."""

    FEATURE = "FEATURE"
    """Feature-spezifische Konfiguration aus feature/meta.json."""

    # Zukünftige Scopes (auskommentiert für MVP)
    # USER = "USER"
    # """User-spezifische Preferences (überschreibt FEATURE + GLOBAL)."""
    #
    # SYSTEM = "SYSTEM"
    # """System-Konfiguration (nur für Admins änderbar)."""