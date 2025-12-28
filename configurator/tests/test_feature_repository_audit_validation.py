"""
Zusätzliche Tests für FeatureRepository:  Audit-Validierung.

Diese Tests stellen sicher, dass audit-Konfiguration in meta.json
korrekt validiert wird und typische Fehler sauber als InvalidMetaException
reportet werden.
"""
from pathlib import Path
from typing import Dict, Any
import pytest

from configurator.exceptions.invalid_meta_exception import InvalidMetaException
from configurator.repository. feature_repository import FeatureRepository
from configurator.tests.conftest import create_meta_json


def _base_meta(feature_id: str) -> Dict[str, Any]:
    """Erstellt ein valides Basis-Meta-Objekt."""
    return {
        "id": feature_id,
        "label": "Test Feature",
        "version":  "1.0.0",
        "main_class": "some.module.Class",
        "visible_for":  ["ADMIN"],
        "is_core": False,
        "sort_order": 10,
        "requires_login": True,
        "dependencies": [],
    }


# ===== AUDIT VALIDIERUNG =====

def test_audit_retention_days_must_be_positive(tmp_path: Path) -> None:
    """Test: retention_days muss eine positive Zahl sein."""
    feature_id = "negative_retention"
    meta = _base_meta(feature_id)
    meta["audit"] = {"must_audit": True, "retention_days": -5}

    create_meta_json(tmp_path / feature_id, meta)
    repo = FeatureRepository(features_root=str(tmp_path), strict_mode=True)

    with pytest.raises(InvalidMetaException) as exc_info:
        repo.discover_all()
    assert "retention_days" in str(exc_info.value. reason)
    assert "positive integer" in str(exc_info. value.reason)


def test_audit_retention_days_zero_is_invalid(tmp_path: Path) -> None:
    """Test: retention_days darf nicht 0 sein."""
    feature_id = "zero_retention"
    meta = _base_meta(feature_id)
    meta["audit"] = {"must_audit": True, "retention_days":  0}

    create_meta_json(tmp_path / feature_id, meta)
    repo = FeatureRepository(features_root=str(tmp_path), strict_mode=True)

    with pytest.raises(InvalidMetaException) as exc_info:
        repo.discover_all()
    assert "retention_days" in str(exc_info.value. reason)


def test_audit_critical_actions_must_be_list(tmp_path: Path) -> None:
    """Test: critical_actions muss eine Liste sein."""
    feature_id = "invalid_critical_actions"
    meta = _base_meta(feature_id)
    meta["audit"] = {"must_audit": True, "critical_actions": "NOT_A_LIST"}

    create_meta_json(tmp_path / feature_id, meta)
    repo = FeatureRepository(features_root=str(tmp_path), strict_mode=True)

    with pytest.raises(InvalidMetaException) as exc_info:
        repo.discover_all()
    assert "critical_actions" in str(exc_info. value.reason)
    assert "list" in str(exc_info.value.reason)


def test_audit_min_log_level_must_be_valid(tmp_path: Path) -> None:
    """Test: min_log_level muss ein gültiger Logging-Level sein."""
    feature_id = "invalid_log_level"
    meta = _base_meta(feature_id)
    meta["audit"] = {"must_audit": True, "min_log_level": "INVALID"}

    create_meta_json(tmp_path / feature_id, meta)
    repo = FeatureRepository(features_root=str(tmp_path), strict_mode=True)

    with pytest.raises(InvalidMetaException) as exc_info:
        repo. discover_all()
    assert "min_log_level" in str(exc_info.value.reason)


def test_audit_must_be_dict(tmp_path: Path) -> None:
    """Test: audit muss ein Objekt/Dict sein."""
    feature_id = "audit_not_dict"
    meta = _base_meta(feature_id)
    meta["audit"] = "NOT_A_DICT"

    create_meta_json(tmp_path / feature_id, meta)
    repo = FeatureRepository(features_root=str(tmp_path), strict_mode=True)

    with pytest.raises(InvalidMetaException) as exc_info:
        repo.discover_all()
    assert "audit" in str(exc_info. value.reason)
    assert "dict" in str(exc_info. value.reason)


def test_audit_must_audit_must_be_boolean(tmp_path: Path) -> None:
    """Test: must_audit muss ein Boolean sein."""
    feature_id = "must_audit_not_bool"
    meta = _base_meta(feature_id)
    meta["audit"] = {"must_audit": "yes"}

    create_meta_json(tmp_path / feature_id, meta)
    repo = FeatureRepository(features_root=str(tmp_path), strict_mode=True)

    with pytest.raises(InvalidMetaException) as exc_info:
        repo.discover_all()
    assert "must_audit" in str(exc_info.value.reason)
    assert "boolean" in str(exc_info.value.reason)


def test_audit_valid_configuration(tmp_path: Path) -> None:
    """Test: Valide Audit-Konfiguration wird akzeptiert."""
    feature_id = "valid_audit"
    meta = _base_meta(feature_id)
    meta["audit"] = {
        "must_audit": True,
        "min_log_level": "WARNING",
        "critical_actions":  ["DELETE", "UPDATE"],
        "retention_days":  730,
    }

    create_meta_json(tmp_path / feature_id, meta)
    repo = FeatureRepository(features_root=str(tmp_path), strict_mode=True)

    descriptors = repo.discover_all()
    assert len(descriptors) == 1
    assert descriptors[0].audit is not None
    assert descriptors[0].audit.must_audit is True
    assert descriptors[0].audit.min_log_level == "WARNING"
    assert descriptors[0].audit.critical_actions == ["DELETE", "UPDATE"]
    assert descriptors[0]. audit.retention_days == 730


# ===== GRUNDLEGENDE VALIDIERUNG =====

def test_id_must_match_folder_name(tmp_path: Path) -> None:
    """Test: ID in meta.json muss mit Ordnernamen übereinstimmen."""
    folder_name = "my_feature"
    meta = _base_meta("wrong_id")  # ID stimmt nicht mit Ordner überein

    create_meta_json(tmp_path / folder_name, meta)
    repo = FeatureRepository(features_root=str(tmp_path), strict_mode=True)

    with pytest.raises(InvalidMetaException) as exc_info:
        repo.discover_all()
    assert "ID mismatch" in str(exc_info.value.reason)
    assert "my_feature" in str(exc_info.value.reason)
    assert "wrong_id" in str(exc_info.value.reason)


def test_version_must_follow_semantic_versioning(tmp_path: Path) -> None:
    """Test: Version muss Semantic Versioning (X.Y.Z) folgen."""
    feature_id = "invalid_version"
    meta = _base_meta(feature_id)
    meta["version"] = "1.0"  # Fehlendes Patch-Level

    create_meta_json(tmp_path / feature_id, meta)
    repo = FeatureRepository(features_root=str(tmp_path), strict_mode=True)

    with pytest.raises(InvalidMetaException) as exc_info:
        repo. discover_all()
    assert "semantic versioning" in str(exc_info.value.reason)


def test_visible_for_must_be_list(tmp_path: Path) -> None:
    """Test: visible_for muss eine Liste sein."""
    feature_id = "invalid_visible_for"
    meta = _base_meta(feature_id)
    meta["visible_for"] = "NOT_A_LIST"

    create_meta_json(tmp_path / feature_id, meta)
    repo = FeatureRepository(features_root=str(tmp_path), strict_mode=True)

    with pytest.raises(InvalidMetaException) as exc_info:
        repo.discover_all()
    assert "visible_for" in str(exc_info.value.reason)
    assert "list" in str(exc_info.value. reason)


def test_dependencies_must_be_list(tmp_path: Path) -> None:
    """Test: dependencies muss eine Liste sein."""
    feature_id = "invalid_dependencies"
    meta = _base_meta(feature_id)
    meta["dependencies"] = "NOT_A_LIST"

    create_meta_json(tmp_path / feature_id, meta)
    repo = FeatureRepository(features_root=str(tmp_path), strict_mode=True)

    with pytest.raises(InvalidMetaException) as exc_info:
        repo.discover_all()
    assert "dependencies" in str(exc_info.value.reason)
    assert "list" in str(exc_info.value.reason)


def test_is_core_must_be_boolean(tmp_path: Path) -> None:
    """Test: is_core muss ein Boolean sein."""
    feature_id = "invalid_is_core"
    meta = _base_meta(feature_id)
    meta["is_core"] = "yes"

    create_meta_json(tmp_path / feature_id, meta)
    repo = FeatureRepository(features_root=str(tmp_path), strict_mode=True)

    with pytest.raises(InvalidMetaException) as exc_info:
        repo.discover_all()
    assert "is_core" in str(exc_info.value.reason)
    assert "boolean" in str(exc_info.value.reason)


def test_requires_login_must_be_boolean(tmp_path: Path) -> None:
    """Test: requires_login muss ein Boolean sein."""
    feature_id = "invalid_requires_login"
    meta = _base_meta(feature_id)
    meta["requires_login"] = "yes"

    create_meta_json(tmp_path / feature_id, meta)
    repo = FeatureRepository(features_root=str(tmp_path), strict_mode=True)

    with pytest.raises(InvalidMetaException) as exc_info:
        repo.discover_all()
    assert "requires_login" in str(exc_info.value.reason)
    assert "boolean" in str(exc_info.value.reason)


def test_sort_order_must_be_non_negative_integer(tmp_path: Path) -> None:
    """Test: sort_order muss eine nicht-negative Ganzzahl sein."""
    feature_id = "invalid_sort_order"
    meta = _base_meta(feature_id)
    meta["sort_order"] = -10

    create_meta_json(tmp_path / feature_id, meta)
    repo = FeatureRepository(features_root=str(tmp_path), strict_mode=True)

    with pytest.raises(InvalidMetaException) as exc_info:
        repo. discover_all()
    assert "sort_order" in str(exc_info.value.reason)
    assert "non-negative integer" in str(exc_info. value.reason)


def test_sort_order_must_be_integer_not_string(tmp_path: Path) -> None:
    """Test: sort_order muss Integer sein, kein String."""
    feature_id = "sort_order_string"
    meta = _base_meta(feature_id)
    meta["sort_order"] = "10"

    create_meta_json(tmp_path / feature_id, meta)
    repo = FeatureRepository(features_root=str(tmp_path), strict_mode=True)

    with pytest.raises(InvalidMetaException) as exc_info:
        repo.discover_all()
    assert "sort_order" in str(exc_info.value.reason)