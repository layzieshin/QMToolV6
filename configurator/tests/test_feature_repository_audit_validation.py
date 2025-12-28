"""
Zusätzliche Tests für FeatureRepository: Audit-Validierung.

Diese Tests stellen sicher, dass audit-Konfiguration in meta.json
korrekt validiert wird und typische Fehler sauber als InvalidMetaException
reportet werden.
"""
from pathlib import Path
from typing import Dict, Any
import pytest

from configurator.exceptions.invalid_meta_exception import InvalidMetaException
from configurator.repository.feature_repository import FeatureRepository
from configurator.tests.conftest import create_meta_json


def _base_meta(feature_id: str) -> Dict[str, Any]:
    return {
        "id": feature_id,
        "label": "Test Feature",
        "version": "1.0.0",
        "main_class": "some.module.Class",
        "visible_for": ["ADMIN"],
        "is_core": False,
        "sort_order": 10,
        "requires_login": True,
        "dependencies": [],
    }


def test_audit_retention_days_must_be_positive(tmp_path: Path) -> None:
    feature_id = "negative_retention"
    meta = _base_meta(feature_id)
    meta["audit"] = {"must_audit": True, "retention_days": -5}

    create_meta_json(tmp_path / feature_id, meta)
    repo = FeatureRepository(features_root=str(tmp_path))

    with pytest.raises(InvalidMetaException):
        repo.discover_all()


def test_audit_critical_actions_must_be_list(tmp_path: Path) -> None:
    feature_id = "invalid_critical_actions"
    meta = _base_meta(feature_id)
    meta["audit"] = {"must_audit": True, "critical_actions": "NOT_A_LIST"}

    create_meta_json(tmp_path / feature_id, meta)
    repo = FeatureRepository(features_root=str(tmp_path))

    with pytest.raises(InvalidMetaException):
        repo.discover_all()