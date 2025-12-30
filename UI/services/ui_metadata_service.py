"""Service for loading metadata and labels for the UI."""
from __future__ import annotations

import json
from pathlib import Path
from typing import List, Dict

from configurator.services.configurator_service_interface import ConfiguratorServiceInterface
from UI.exceptions.ui_exceptions import UIDataLoadError


class UIMetadataService:
    """Loads meta.json descriptors and labels.tsv content."""

    def __init__(self, configurator: ConfiguratorServiceInterface, labels_path: Path) -> None:
        self._configurator = configurator
        self._labels_path = labels_path

    def load_meta_json(self) -> str:
        """Return a formatted JSON string of discovered feature descriptors."""
        descriptors = self._configurator.discover_features()
        payload = [self._descriptor_to_dict(d) for d in descriptors]
        return json.dumps(payload, indent=2, ensure_ascii=False)

    def load_labels_tsv(self) -> str:
        """Return the raw labels.tsv contents."""
        if not self._labels_path.exists():
            raise UIDataLoadError(f"labels.tsv nicht gefunden: {self._labels_path}")
        try:
            return self._labels_path.read_text(encoding="utf-8")
        except OSError as exc:
            raise UIDataLoadError(f"labels.tsv konnte nicht gelesen werden: {exc}") from exc

    @staticmethod
    def _descriptor_to_dict(descriptor) -> Dict:
        return {
            "id": descriptor.id,
            "label": descriptor.label,
            "version": descriptor.version,
            "main_class": descriptor.main_class,
            "visible_for": list(descriptor.visible_for),
            "is_core": descriptor.is_core,
            "sort_order": descriptor.sort_order,
            "requires_login": descriptor.requires_login,
            "dependencies": list(descriptor.dependencies),
            "audit": UIMetadataService._audit_to_dict(descriptor.audit),
            "description": descriptor.description,
            "icon": descriptor.icon,
        }

    @staticmethod
    def _audit_to_dict(audit) -> Dict | None:
        if audit is None:
            return None
        return {
            "must_audit": audit.must_audit,
            "min_log_level": audit.min_log_level,
            "critical_actions": audit.critical_actions,
            "retention_days": audit.retention_days,
        }
