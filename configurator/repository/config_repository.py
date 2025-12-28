"""
ConfigRepository - Lädt globale App-Konfiguration.

Lädt config/app_config.json und merged mit Defaults.

Author: QMToolV6 Development Team
Version: 1.1.0
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict

from configurator.dto.app_config_dto import AppConfigDTO
from configurator.exceptions.config_validation_exception import ConfigValidationException

logger = logging. getLogger(__name__)


class ConfigRepository:
    """
    Read-only App-Config aus `config/app_config.json` (MVP).

    Lädt zentrale Anwendungskonfiguration:
    - Datenbank-Pfad
    - Audit-Defaults
    - Session-Einstellungen
    - Pfade (Features, Data, Temp)

    Falls config/app_config.json nicht existiert, werden Defaults verwendet.

    Usage:
        >>> repo = ConfigRepository(project_root=".")
        >>> config = repo.load_app_config()
        >>> print(config.db_path)  # "qmtool.db"
    """

    def __init__(self, project_root: str = "."):
        """
        Initialisiert Repository.

        Args:
            project_root: Root-Verzeichnis des Projekts
        """
        self._project_root = Path(project_root).resolve()
        logger.info(f"ConfigRepository initialized with root: {self._project_root}")

    def load_app_config(self, strict: bool = False) -> AppConfigDTO:
        """
        Lädt App-Konfiguration aus config/app_config.json.

        Args:
            strict: Wenn True, wirft Exception bei ungültiger Config.
                   Wenn False, verwendet Defaults und loggt Warnung.

        Returns:
            AppConfigDTO mit Konfiguration

        Raises:
            ConfigValidationException:  Nur wenn strict=True und Config ungültig

        Example config/app_config.json:
            {
                "app_name": "QMToolV6",
                "app_version": "1.0.0",
                "database": {
                    "path": "production.db"
                },
                "audit": {
                    "default_log_level": "WARNING",
                    "default_retention_days": 730
                },
                "session":  {
                    "timeout_minutes": 30,
                    "max_failed_logins": 3
                },
                "paths":  {
                    "features_root": ".",
                    "data_dir": "./data",
                    "temp_dir": "./temp"
                }
            }
        """
        config_path = self._project_root / "config" / "app_config.json"

        # Defaults
        dto = AppConfigDTO()

        # Datei nicht vorhanden → Defaults verwenden
        if not config_path.exists():
            logger.info("No app_config.json found, using defaults")
            return dto

        # JSON laden
        try:
            raw_text = config_path.read_text(encoding="utf-8")
            raw = json.loads(raw_text)

            if not isinstance(raw, dict):
                error_msg = "app_config.json root must be a JSON object"
                if strict:
                    raise ConfigValidationException(
                        "app_config.json",  # ✅ NEU
                        type(raw).__name__,
                        error_msg
                    )
                logger.warning(f"{error_msg}, using defaults")
                return dto

            logger.info(f"Loaded app_config.json from {config_path}")

        except json.JSONDecodeError as e:
            error_msg = f"Invalid JSON in app_config.json: {e}"
            if strict:
                raise ConfigValidationException(
                    "app_config.json",
                    None,
                    f"JSON parsing failed: {e}"
                ) from e
            logger.error(f"{error_msg}, using defaults")
            return dto

        except Exception as e:
            error_msg = f"Error reading app_config.json: {e}"
            if strict:
                raise ConfigValidationException(
                    "app_config.json",
                    None,
                    f"File read error: {e}"
                ) from e
            logger.error(f"{error_msg}, using defaults")
            return dto

        # Sections extrahieren
        database = raw.get("database") or {}
        audit = raw.get("audit") or {}
        session = raw.get("session") or {}
        paths = raw.get("paths") or {}

        # DTO mit Overrides erstellen
        try:
            dto = AppConfigDTO(
                app_name=self._get_string(raw, "app_name", dto.app_name),
                app_version=self._get_string(raw, "app_version", dto.app_version),
                db_path=self._get_string(database, "path", dto. db_path),
                default_log_level=self._get_string(
                    audit,
                    "default_log_level",
                    dto.default_log_level
                ),
                default_retention_days=self._get_int(
                    audit,
                    "default_retention_days",
                    dto.default_retention_days,
                    min_value=1
                ),
                features_root=self._get_string(paths, "features_root", dto.features_root),
                data_dir=self._get_string(paths, "data_dir", dto.data_dir),
                temp_dir=self._get_string(paths, "temp_dir", dto.temp_dir),
                session_timeout_minutes=self._get_int(
                    session,
                    "timeout_minutes",
                    dto. session_timeout_minutes,
                    min_value=1
                ),
                max_failed_logins=self._get_int(
                    session,
                    "max_failed_logins",
                    dto.max_failed_logins,
                    min_value=1
                ),
            )

            # Validierung
            dto.validate()

            logger.info("App config loaded and validated successfully")
            return dto

        except ValueError as e:
            # ValueError von AppConfigDTO. validate()
            error_msg = f"Invalid values in app_config.json: {e}"
            if strict:
                # Extrahiere Feldname aus ValueError message
                field = str(e).split()[0] if " " in str(e) else "unknown"
                raise ConfigValidationException(
                    field,
                    None,
                    str(e)
                ) from e
            logger.error(f"{error_msg}, using defaults")
            return AppConfigDTO()

    def _get_string(
        self,
        section: Dict[str, Any],
        key: str,
        default: str
    ) -> str:
        """
        Extrahiert String-Wert aus Section.

        Args:
            section: Dict-Section aus app_config.json
            key: Key im Dict
            default: Default-Wert falls nicht vorhanden

        Returns:
            String-Wert oder Default
        """
        value = section.get(key)
        if value is None:
            return default
        return str(value)

    def _get_int(
        self,
        section: Dict[str, Any],
        key: str,
        default: int,
        min_value: int | None = None
    ) -> int:
        """
        Extrahiert Int-Wert aus Section mit optionaler Min-Validierung.

        Args:
            section: Dict-Section aus app_config.json
            key: Key im Dict
            default:  Default-Wert falls nicht vorhanden
            min_value:  Minimaler erlaubter Wert (optional)

        Returns:
            Int-Wert oder Default
        """
        value = section.get(key)
        if value is None:
            return default

        try:
            int_value = int(value)

            # Min-Value Check
            if min_value is not None and int_value < min_value:
                logger.warning(
                    f"Value for {key} ({int_value}) is below minimum ({min_value}), "
                    f"using default {default}"
                )
                return default

            return int_value

        except (ValueError, TypeError):
            logger.warning(
                f"Invalid int value for {key}: {value}, using default {default}"
            )
            return default