"""
FeatureRepository - Discovery und Validierung von Features.

Scannt Level-1 Ordner nach meta.json, cached Descriptors und validiert Konventionen.

Author: QMToolV6 Development Team
Version: 1.0.0
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any

from configurator.dto.audit_config_dto import AuditConfigDTO
from configurator.dto.feature_descriptor_dto import FeatureDescriptorDTO
from configurator.exceptions.feature_not_found_exception import FeatureNotFoundException
from configurator.exceptions.invalid_meta_exception import InvalidMetaException

logger = logging.getLogger(__name__)


class FeatureRepository:
    """
    Discovery + Load + Validate von `<feature_id>/meta.json` (Level-1).

    Verantwortlichkeiten:
    - Scannt features_root nach Level-1 Ordnern
    - Ignoriert konfigurierte System-Ordner
    - Lädt und validiert meta.json
    - Cached Descriptors für Performance
    - Erzwingt Konvention:  id == Ordnername

    Usage:
        >>> repo = FeatureRepository(features_root=".")
        >>> descriptors = repo.discover_all()
        >>> auth_meta = repo.get_by_id("authenticator")
        >>> is_valid = repo.validate("authenticator")
    """

    # Ordner, die ignoriert werden (keine Features)
    IGNORE_FOLDERS = {
        "shared",  # Gemeinsame Infrastruktur
        ". idea",  # IDE-Konfiguration
        ". venv",  # Virtual Environment
        "venv",  # Virtual Environment (alternative)
        "__pycache__",  # Python Bytecode
        ".pytest_cache",  # pytest Cache
        "tests",  # Root-Tests (Feature-Tests sind in Feature/)
        ". git",  # Git-Metadaten
        "docs",  # Dokumentation
        "htmlcov",  # Coverage-Reports
        "config",  # Globale Konfiguration
        "data",  # Daten-Verzeichnis
        "temp",  # Temp-Verzeichnis
    }

    def __init__(self, features_root: str = "."):
        """
        Initialisiert Repository.

        Args:
            features_root: Root-Verzeichnis für Feature-Discovery
        """
        self._features_root = Path(features_root).resolve()
        self._cache: Dict[str, FeatureDescriptorDTO] = {}
        logger.info(f"FeatureRepository initialized with root: {self._features_root}")

    def discover_all(self) -> List[FeatureDescriptorDTO]:
        """
        Scannt features_root nach Level-1 Features.

        Prozess:
        1. Iteriert über alle Unterordner
        2. Ignoriert IGNORE_FOLDERS
        3. Prüft auf meta.json
        4. Lädt und validiert meta.json
        5. Cached Descriptor

        Returns:
            Liste aller gefundenen Feature-Descriptors

        Raises:
            InvalidMetaException: Wenn meta. json ungültig ist
        """
        if not self._features_root.exists() or not self._features_root.is_dir():
            logger.warning(f"Features root does not exist: {self._features_root}")
            return []

        descriptors: List[FeatureDescriptorDTO] = []

        for child in sorted(self._features_root.iterdir()):
            # Nur Verzeichnisse
            if not child.is_dir():
                continue

            # Ignorierte Ordner überspringen
            if child.name in self.IGNORE_FOLDERS:
                logger.debug(f"Ignoring folder: {child.name}")
                continue

            # meta.json muss existieren
            meta_path = child / "meta.json"
            if not meta_path.exists():
                logger.debug(f"No meta.json in:  {child.name}")
                continue

            try:
                descriptor = self._load_and_validate(
                    meta_path=meta_path,
                    folder_name=child.name
                )
                self._cache[descriptor.id] = descriptor
                descriptors.append(descriptor)
                logger.info(f"Discovered feature: {descriptor.id} v{descriptor.version}")
            except InvalidMetaException as e:
                logger.error(f"Invalid meta.json in {child.name}: {e.reason}")
                raise

        logger.info(f"Discovery complete:  {len(descriptors)} features found")
        return descriptors

    def get_by_id(self, feature_id: str) -> FeatureDescriptorDTO:
        """
        Lädt Feature-Descriptor nach ID.

        Prüft zuerst Cache, dann lädt aus meta.json.

        Args:
            feature_id: ID des Features (muss Ordnername sein)

        Returns:
            FeatureDescriptorDTO

        Raises:
            FeatureNotFoundException: Wenn Feature nicht existiert
            InvalidMetaException: Wenn meta.json ungültig ist
        """
        # Cache-Lookup
        if feature_id in self._cache:
            logger.debug(f"Cache hit for feature: {feature_id}")
            return self._cache[feature_id]

        # meta.json laden
        meta_path = self._features_root / feature_id / "meta.json"
        if not meta_path.exists():
            logger.error(f"Feature not found: {feature_id}")
            raise FeatureNotFoundException(feature_id)

        descriptor = self._load_and_validate(
            meta_path=meta_path,
            folder_name=feature_id
        )

        # Cache aktualisieren
        self._cache[descriptor.id] = descriptor
        logger.info(f"Loaded feature from meta.json: {feature_id}")
        return descriptor

    def validate(self, feature_id: str) -> bool:
        """
        Validiert meta.json eines Features.

        Args:
            feature_id: ID des zu validierenden Features

        Returns:
            True wenn valid

        Raises:
            FeatureNotFoundException: Wenn Feature nicht existiert
            InvalidMetaException: Wenn meta.json ungültig ist
        """
        _ = self.get_by_id(feature_id)  # Lädt und validiert
        logger.info(f"Feature validation successful: {feature_id}")
        return True

    def _load_and_validate(
            self,
            meta_path: Path,
            folder_name: str
    ) -> FeatureDescriptorDTO:
        """
        Lädt meta.json und validiert alle Felder.

        Args:
            meta_path:  Pfad zur meta.json
            folder_name: Name des Feature-Ordners

        Returns:
            Validierter FeatureDescriptorDTO

        Raises:
            InvalidMetaException: Bei Validierungsfehlern
        """
        # JSON laden
        try:
            raw_text = meta_path.read_text(encoding="utf-8")
            raw = json.loads(raw_text)
        except json.JSONDecodeError as e:
            raise InvalidMetaException(
                folder_name,
                f"JSON-Parsing fehlgeschlagen: {e}"
            ) from e
        except Exception as e:
            raise InvalidMetaException(
                folder_name,
                f"meta.json nicht lesbar: {e}"
            ) from e

        # Root muss Dict sein
        if not isinstance(raw, dict):
            raise InvalidMetaException(
                folder_name,
                "Root muss ein JSON-Objekt sein"
            )

        # Pflichtfelder validieren
        self._validate_required_fields(raw=raw, feature_id=folder_name)

        # id muss Ordnername sein
        meta_id = raw.get("id")
        if meta_id != folder_name:
            raise InvalidMetaException(
                folder_name,
                f"`id` muss dem Ordnernamen entsprechen "
                f"(meta.json hat id='{meta_id}', erwartet '{folder_name}')"
            )

        # Audit-Config parsen
        audit_dto = self._parse_audit(
            feature_id=folder_name,
            raw_audit=raw.get("audit")
        )

        # DTO erstellen
        try:
            return FeatureDescriptorDTO(
                id=str(raw["id"]),
                label=str(raw["label"]),
                version=str(raw["version"]),
                main_class=str(raw["main_class"]),
                visible_for=self._parse_string_list(
                    raw.get("visible_for"),
                    "visible_for",
                    folder_name
                ),
                is_core=bool(raw.get("is_core", False)),
                sort_order=int(raw.get("sort_order", 999)),
                requires_login=bool(raw.get("requires_login", True)),
                dependencies=self._parse_string_list(
                    raw.get("dependencies"),
                    "dependencies",
                    folder_name
                ),
                audit=audit_dto,
                description=self._parse_optional_string(raw.get("description")),
                icon=self._parse_optional_string(raw.get("icon")),
            )
        except (ValueError, TypeError) as e:
            raise InvalidMetaException(
                folder_name,
                f"Fehler beim Erstellen des DTOs: {e}"
            ) from e

    def _validate_required_fields(
            self,
            raw: Dict[str, Any],
            feature_id: str
    ) -> None:
        """
        Validiert Pflichtfelder in meta.json.

        Args:
            raw: Geparstes JSON-Dict
            feature_id: Feature-ID für Fehlermeldungen

        Raises:
            InvalidMetaException: Bei fehlenden oder invaliden Feldern
        """
        required_fields = ["id", "label", "version", "main_class"]

        # Felder müssen existieren
        for field in required_fields:
            if field not in raw:
                raise InvalidMetaException(
                    feature_id,
                    f"Pflichtfeld fehlt: {field}"
                )

        # Felder müssen nicht-leere Strings sein
        for field in required_fields:
            value = raw[field]
            if not isinstance(value, str) or not value.strip():
                raise InvalidMetaException(
                    feature_id,
                    f"Pflichtfeld `{field}` muss ein nicht-leerer String sein"
                )

    def _parse_audit(
            self,
            feature_id: str,
            raw_audit: Any
    ) -> Optional[AuditConfigDTO]:
        """
        Parst audit-Konfiguration aus meta. json.

        Args:
            feature_id: Feature-ID für Fehlermeldungen
            raw_audit: Roh-Wert aus meta.json["audit"]

        Returns:
            AuditConfigDTO oder None

        Raises:
            InvalidMetaException: Bei ungültiger Audit-Config
        """
        if raw_audit is None:
            return None

        if not isinstance(raw_audit, dict):
            raise InvalidMetaException(
                feature_id,
                "`audit` muss ein Objekt sein"
            )

        # must_audit
        must_audit = bool(raw_audit.get("must_audit", False))

        # min_log_level
        min_log_level = raw_audit.get("min_log_level", "INFO")
        if not isinstance(min_log_level, str) or not min_log_level.strip():
            raise InvalidMetaException(
                feature_id,
                "`audit.min_log_level` muss ein nicht-leerer String sein"
            )

        # critical_actions
        critical_actions_raw = raw_audit.get("critical_actions")
        critical_actions = self._parse_string_list(
            critical_actions_raw,
            "audit.critical_actions",
            feature_id
        )

        # retention_days
        retention_days = raw_audit.get("retention_days", 365)
        if not isinstance(retention_days, int):
            try:
                retention_days = int(retention_days)
            except (ValueError, TypeError):
                raise InvalidMetaException(
                    feature_id,
                    "`audit.retention_days` muss eine Ganzzahl sein"
                )

        if retention_days <= 0:
            raise InvalidMetaException(
                feature_id,
                f"`audit.retention_days` muss > 0 sein, ist aber {retention_days}"
            )

        # DTO erstellen (mit Validierung)
        try:
            return AuditConfigDTO(
                must_audit=must_audit,
                min_log_level=min_log_level,
                critical_actions=critical_actions,
                retention_days=retention_days,
            )
        except ValueError as e:
            raise InvalidMetaException(
                feature_id,
                f"Ungültige Audit-Konfiguration: {e}"
            ) from e

    def _parse_string_list(
            self,
            value: Any,
            field_name: str,
            feature_id: str
    ) -> List[str]:
        """
        Parst optionale String-Liste.

        Args:
            value: Roh-Wert aus JSON
            field_name: Feldname für Fehlermeldungen
            feature_id: Feature-ID für Fehlermeldungen

        Returns:
            Liste von Strings (leer falls None)

        Raises:
            InvalidMetaException:  Wenn Wert kein String-Array ist
        """
        if value is None:
            return []

        if not isinstance(value, list):
            raise InvalidMetaException(
                feature_id,
                f"`{field_name}` muss ein Array sein"
            )

        # Alle Elemente müssen Strings sein
        if not all(isinstance(x, str) for x in value):
            raise InvalidMetaException(
                feature_id,
                f"`{field_name}` muss ein Array von Strings sein"
            )

        return [str(x) for x in value]

    def _parse_optional_string(self, value: Any) -> Optional[str]:
        """
        Parst optionalen String.

        Args:
            value: Roh-Wert aus JSON

        Returns:
            String oder None
        """
        if value is None:
            return None
        return str(value) if value else None