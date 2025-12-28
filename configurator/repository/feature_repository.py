"""
FeatureRepository - Discovery und Validierung von Features.

Scannt Level-1 Ordner nach meta.json, cached Descriptors und validiert Konventionen.

Author: QMToolV6 Development Team
Version: 1.1.0
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
    - Scannt features_root nach Level-1 Ordnern.
    - Ignoriert konfigurierte System-Ordner.
    - Lädt und validiert meta.json.
    - Cached Descriptors für bessere Performance.
    - Erzwingt Konvention: id == Ordnername.

    Usage:
        >>> repo = FeatureRepository(features_root=".")
        >>> descriptors = repo.discover_all()
        >>> auth_meta = repo.get_by_id("authenticator")
        >>> is_valid = repo.validate("authenticator")
    """

    # Ordner, die ignoriert werden (keine Features)
    IGNORE_FOLDERS = {
        "shared",
        ".idea",
        ".venv",
        "venv",
        "__pycache__",
        ".pytest_cache",
        "tests",
        ".git",
        "docs",
        "htmlcov",
        "config",
        "data",
        "temp",
    }

    def __init__(self, features_root: str = "."):
        """
        Initialisiert das Repository.

        Args:
            features_root: Root-Verzeichnis für Feature-Discovery.
        """
        self._features_root = Path(features_root).resolve()
        self._cache: Dict[str, FeatureDescriptorDTO] = {}
        logger.info(f"FeatureRepository initialized with root: {self._features_root}")

    def discover_all(self) -> List[FeatureDescriptorDTO]:
        """
        Scannt features_root nach Level-1 Features.

        Prozess:
        1. Iteriert über alle Unterordner.
        2. Ignoriert IGNORE_FOLDERS.
        3. Prüft auf meta.json.
        4. Lädt und validiert meta.json.
        5. Cached Descriptor.

        Returns:
            Liste aller gefundenen Feature-Descriptors.

        Raises:
            InvalidMetaException: Wenn meta.json ungültig ist.
        """
        if not self._features_root.exists() or not self._features_root.is_dir():
            logger.warning(f"Features root does not exist: {self._features_root}")
            return []

        descriptors: List[FeatureDescriptorDTO] = []

        for child in sorted(self._features_root.iterdir()):
            if not child.is_dir() or child.name in self.IGNORE_FOLDERS:
                logger.debug(f"Ignoring non-feature folder: {child.name}")
                continue

            meta_path = child / "meta.json"
            if not meta_path.exists():
                logger.debug(f"meta.json not found in: {child.name}")
                continue

            try:
                descriptor = self._load_and_validate(meta_path=meta_path, folder_name=child.name)
                self._cache[descriptor.id] = descriptor
                descriptors.append(descriptor)
                logger.info(f"Discovered feature: {descriptor.id} v{descriptor.version}")
            except InvalidMetaException as e:
                logger.error(f"Invalid meta.json in {child.name}: {e.reason}")

        logger.info(f"Discovery complete: {len(descriptors)} features found.")
        return descriptors

    def get_by_id(self, feature_id: str) -> FeatureDescriptorDTO:
        """
        Lädt den Feature-Descriptor nach ID.

        Args:
            feature_id: ID des Features (entspricht Ordnername).

        Returns:
            FeatureDescriptorDTO.

        Raises:
            FeatureNotFoundException: Wenn Feature oder meta.json nicht existiert.
            InvalidMetaException: Wenn meta.json ungültig ist.
        """
        if feature_id in self._cache:
            return self._cache[feature_id]

        meta_path = self._features_root / feature_id / "meta.json"
        if not meta_path.exists():
            raise FeatureNotFoundException(feature_id)

        descriptor = self._load_and_validate(meta_path=meta_path, folder_name=feature_id)
        self._cache[descriptor.id] = descriptor
        return descriptor

    def validate(self, feature_id: str) -> bool:
        """
        Validiert meta.json eines Features.

        Args:
            feature_id: ID des zu validierenden Features.

        Returns:
            True wenn valid.

        Raises:
            FeatureNotFoundException: Wenn Feature nicht gefunden wird.
            InvalidMetaException: Wenn meta.json ungültig ist.
        """
        _ = self.get_by_id(feature_id)
        return True

    def _load_and_validate(self, meta_path: Path, folder_name: str) -> FeatureDescriptorDTO:
        """
        Lädt meta.json und validiert alle Felder.

        Args:
            meta_path: Pfad zur meta.json.
            folder_name: Name des Ordners.

        Returns:
            Valider FeatureDescriptorDTO.

        Raises:
            InvalidMetaException: Bei Validierungsfehlern.
        """
        try:
            raw = json.loads(meta_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            raise InvalidMetaException(folder_name, f"JSON parsing error: {e}") from e

        self._validate_required_fields(raw=raw, feature_id=folder_name)
        audit_dto = self._parse_audit(folder_name, raw.get("audit"))
        return FeatureDescriptorDTO(
            id=raw["id"],
            label=raw["label"],
            version=raw["version"],
            main_class=raw["main_class"],
            visible_for=raw.get("visible_for", []),
            is_core=raw.get("is_core", False),
            sort_order=raw.get("sort_order", 999),
            requires_login=raw.get("requires_login", True),
            dependencies=raw.get("dependencies", []),
            audit=audit_dto,
            description=raw.get("description"),
            icon=raw.get("icon"),
        )

    def _validate_required_fields(self, raw: Dict[str, Any], feature_id: str) -> None:
        """
        Validiert Pflichtfelder in meta.json.

        Args:
            raw: Geladene meta.json Daten.
            feature_id: ID des Features.

        Raises:
            InvalidMetaException: Bei Fehlenden oder ungültigen Feldern.
        """
        required_fields = ["id", "label", "version", "main_class"]
        for field in required_fields:
            if not raw.get(field):
                raise InvalidMetaException(feature_id, f"Missing required field: {field}")

    def _parse_audit(self, feature_id: str, raw_audit: Any) -> Optional[AuditConfigDTO]:
        """
        Parst audit-Konfiguration aus meta.json.

        Returns:
            AuditConfigDTO oder None.

        Raises:
            InvalidMetaException: Bei fehlerhafter Audit-Konfiguration.
        """
        if not raw_audit:
            return None

        return AuditConfigDTO(
            must_audit=raw_audit.get("must_audit", False),
            min_log_level=raw_audit.get("min_log_level", "INFO"),
            critical_actions=raw_audit.get("critical_actions", []),
            retention_days=raw_audit.get("retention_days", 365),
        )