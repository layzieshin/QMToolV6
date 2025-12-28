"""
AppConfigDTO - Globale Anwendungskonfiguration.

Kapselt alle zentralen Einstellungen aus config/app_config.json.

Author: QMToolV6 Development Team
Version: 1.1.0
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class AppConfigDTO:
    """
    Globale App-Konfiguration (Defaults + Override aus `config/app_config.json`).

    Struktur der config/app_config.json:
        {
            "app_name": "QMToolV6",
            "app_version": "0.1.0",
            "database":  {
                "path": "qmtool. db"
            },
            "audit":  {
                "default_log_level": "INFO",
                "default_retention_days": 365
            },
            "session": {
                "timeout_minutes": 60,
                "max_failed_logins": 5
            },
            "paths": {
                "features_root": ".",
                "data_dir": "./data",
                "temp_dir": "./temp"
            }
        }
    """

    # ===== App-Metadaten =====
    app_name: str = "QMToolV6"
    """Name der Anwendung."""

    app_version: str = "0.1.0"
    """Version der Anwendung (Semantic Versioning)."""

    # ===== Datenbank =====
    db_path: str = "qmtool.db"
    """Pfad zur SQLite-Datenbank."""

    # ===== Audit =====
    default_log_level: str = "INFO"
    """Globaler Default-Log-Level für Features ohne eigene Konfiguration."""

    default_retention_days: int = 365
    """Globale Default-Retention in Tagen."""

    # ===== Pfade =====
    features_root: str = "."
    """Root-Verzeichnis für Feature-Discovery."""

    data_dir: str = "./data"
    """Verzeichnis für persistente Daten."""

    temp_dir: str = "./temp"
    """Verzeichnis für temporäre Dateien."""

    # ===== Session =====
    session_timeout_minutes: int = 60
    """Session-Timeout in Minuten."""

    max_failed_logins: int = 5
    """Maximale Anzahl fehlgeschlagener Login-Versuche vor Account-Sperre."""

    def get_db_path(self) -> Path:
        """
        Gibt DB-Pfad als Path-Objekt zurück.

        Returns:
            Path-Objekt zum Datenbank-File
        """
        return Path(self.db_path)

    def get_data_dir(self) -> Path:
        """
        Gibt Daten-Verzeichnis als Path-Objekt zurück.

        Returns:
            Path-Objekt zum Daten-Verzeichnis
        """
        return Path(self.data_dir)

    def get_temp_dir(self) -> Path:
        """
        Gibt Temp-Verzeichnis als Path-Objekt zurück.

        Returns:
            Path-Objekt zum Temp-Verzeichnis
        """
        return Path(self.temp_dir)

    def get_features_root(self) -> Path:
        """
        Gibt Features-Root als Path-Objekt zurück.

        Returns:
            Path-Objekt zum Features-Root-Verzeichnis
        """
        return Path(self.features_root)

    def validate(self) -> None:
        """
        Validiert Konfigurationswerte.

        Raises:
            ValueError: Bei ungültigen Werten (für interne Validierung)

        Note:
            Diese Methode wird intern von AppConfigDTO verwendet.
            ConfigRepository wirft ConfigValidationException bei externen Fehlern.
        """
        if self.session_timeout_minutes <= 0:
            raise ValueError(
                f"session_timeout_minutes must be > 0, got {self.session_timeout_minutes}"
            )

        if self.max_failed_logins <= 0:
            raise ValueError(
                f"max_failed_logins must be > 0, got {self.max_failed_logins}"
            )

        if self.default_retention_days <= 0:
            raise ValueError(
                f"default_retention_days must be > 0, got {self.default_retention_days}"
            )

        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if self.default_log_level not in valid_levels:
            raise ValueError(
                f"default_log_level must be one of {valid_levels}, "
                f"got '{self.default_log_level}'"
            )