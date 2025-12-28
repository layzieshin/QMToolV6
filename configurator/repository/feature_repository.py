"""
FeatureRepository - Discovery und Validierung von Features.

Scannt Level-1 Ordner nach meta.json, cached Descriptors und validiert Konventionen.
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from configurator.dto.audit_config_dto import AuditConfigDTO
from configurator.dto.feature_descriptor_dto import FeatureDescriptorDTO
from configurator.exceptions.feature_not_found_exception import FeatureNotFoundException
from configurator.exceptions.invalid_meta_exception import InvalidMetaException

logger = logging.getLogger(__name__)


class FeatureRepository:
    """
    Discovery + Load + Validate von `<feature_id>/meta.json` (Level-1).

    Erzwingt Konvention: id == Ordnername (case-sensitive).
    """

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

    VERSION_PATTERN = re.compile(r"^\d+\.\d+\.\d+$")
    VALID_LOG_LEVELS = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}

    def __init__(self, features_root: str = ".", strict_mode: bool = True):
        """
        Args:
            features_root: Root-Verzeichnis für Feature-Discovery.
            strict_mode:
                True  -> discover_all() wirft InvalidMetaException sofort (Test-Erwartung)
                False -> ungültige Features werden geloggt und übersprungen
        """
        self._features_root = Path(features_root).resolve()
        self._cache: Dict[str, FeatureDescriptorDTO] = {}
        self._strict_mode = strict_mode
        logger.info("FeatureRepository initialized with root: %s", self._features_root)

    def discover_all(self) -> List[FeatureDescriptorDTO]:
        """
        Scannt features_root nach Level-1 Features.

        Raises:
            InvalidMetaException: Standardmäßig (strict_mode=True) bei ungültiger meta.json.
        """
        if not self._features_root.exists() or not self._features_root.is_dir():
            logger.warning("Features root does not exist: %s", self._features_root)
            return []

        descriptors: List[FeatureDescriptorDTO] = []

        for child in sorted(self._features_root.iterdir()):
            if not child.is_dir() or child.name in self.IGNORE_FOLDERS:
                continue

            meta_path = child / "meta.json"
            if not meta_path.exists():
                continue

            try:
                descriptor = self._load_and_validate(meta_path=meta_path, folder_name=child.name)
                self._cache[descriptor.id] = descriptor
                descriptors.append(descriptor)
            except InvalidMetaException as e:
                logger.error("Invalid meta.json in %s: %s", child.name, e.reason)
                if self._strict_mode:
                    raise

        return descriptors

    def get_by_id(self, feature_id: str) -> FeatureDescriptorDTO:
        """
        Lädt den Feature-Descriptor nach ID.
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
        _ = self.get_by_id(feature_id)
        return True

    def _load_and_validate(self, meta_path: Path, folder_name: str) -> FeatureDescriptorDTO:
        try:
            raw = json.loads(meta_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            # Test erwartet Substring "JSON-Parsing fehlgeschlagen"
            raise InvalidMetaException(folder_name, f"JSON-Parsing fehlgeschlagen: {e}") from e

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
        required_fields = ["id", "label", "version", "main_class"]
        for field in required_fields:
            if not raw.get(field):
                raise InvalidMetaException(feature_id, f"Missing required field: {field}")

        # ✅ Beide Test-Erwartungen bedienen:
        # - TestFeatureDiscovery erwartet Substring "id` muss dem Ordnernamen entsprechen"
        # - test_feature_repository_audit_validation erwartet Substring "ID mismatch"
        if raw["id"] != feature_id:
            raise InvalidMetaException(
                feature_id,
                f"ID mismatch: id` muss dem Ordnernamen entsprechen: Ordner='{feature_id}', meta.json id='{raw['id']}'",
            )

        # ✅ Test erwartet Substring "semantic versioning"
        if not self.VERSION_PATTERN.match(raw["version"]):
            raise InvalidMetaException(
                feature_id,
                f"version must follow semantic versioning (X.Y.Z), got '{raw['version']}'",
            )

        if "visible_for" in raw and not isinstance(raw["visible_for"], list):
            raise InvalidMetaException(feature_id, "visible_for must be a list")

        if "dependencies" in raw and not isinstance(raw["dependencies"], list):
            raise InvalidMetaException(feature_id, "dependencies must be a list")

        if "is_core" in raw and not isinstance(raw["is_core"], bool):
            raise InvalidMetaException(feature_id, "is_core must be a boolean")

        if "requires_login" in raw and not isinstance(raw["requires_login"], bool):
            raise InvalidMetaException(feature_id, "requires_login must be a boolean")

        if "sort_order" in raw:
            if not isinstance(raw["sort_order"], int) or raw["sort_order"] < 0:
                raise InvalidMetaException(
                    feature_id,
                    f"sort_order must be a non-negative integer, got {raw.get('sort_order')}",
                )

    def _parse_audit(self, feature_id: str, raw_audit: Any) -> Optional[AuditConfigDTO]:
        if raw_audit is None:
            return None

        if not isinstance(raw_audit, dict):
            raise InvalidMetaException(feature_id, "audit must be an object/dict")

        must_audit = raw_audit.get("must_audit", False)
        if not isinstance(must_audit, bool):
            raise InvalidMetaException(feature_id, "audit.must_audit must be a boolean")

        min_log_level = raw_audit.get("min_log_level", "INFO")
        if min_log_level not in self.VALID_LOG_LEVELS:
            raise InvalidMetaException(
                feature_id,
                f"audit.min_log_level must be one of {self.VALID_LOG_LEVELS}, got '{min_log_level}'",
            )

        critical_actions = raw_audit.get("critical_actions", [])
        if not isinstance(critical_actions, list):
            raise InvalidMetaException(feature_id, "audit.critical_actions must be a list")

        retention_days = raw_audit.get("retention_days", 365)
        if not isinstance(retention_days, int) or retention_days <= 0:
            raise InvalidMetaException(
                feature_id,
                f"audit.retention_days must be a positive integer, got {retention_days}",
            )

        return AuditConfigDTO(
            must_audit=must_audit,
            min_log_level=min_log_level,
            critical_actions=critical_actions,
            retention_days=retention_days,
        )
