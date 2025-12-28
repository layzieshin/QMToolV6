"""
Integration Tests für ConfiguratorService.

Testet End-to-End Flows des Service.

Author: QMToolV6 Development Team
Version: 1.0.0
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from configurator.dto.feature_registry_dto import FeatureRegistryDTO
from configurator.enum.feature_status import FeatureStatus
from configurator.exceptions.feature_not_found_exception import FeatureNotFoundException
from configurator.services.configurator_service import ConfiguratorService


class TestDiscoverFeatures:
    """Tests für discover_features()."""

    def test_discover_features_returns_all_valid_features(
        self,
        temp_features_root: Path,
        configurator_service: ConfiguratorService,
        sample_feature_meta:  dict
    ) -> None:
        """Discovery gibt alle gültigen Features zurück."""
        # Arrange:   3 Features erstellen
        for feature_id in ["auth", "users", "audit"]:
            meta = sample_feature_meta.copy()
            meta["id"] = feature_id
            meta["label"] = feature_id.title()

            feature_dir = temp_features_root / feature_id
            feature_dir.mkdir(parents=True, exist_ok=True)
            (feature_dir / "meta.json").write_text(
                json.dumps(meta),
                encoding="utf-8"
            )

        # Act
        features = configurator_service.discover_features()

        # Assert
        assert len(features) == 3
        feature_ids = sorted([f.id for f in features])
        assert feature_ids == ["audit", "auth", "users"]


class TestGetFeatureMeta:
    """Tests für get_feature_meta()."""

    def test_get_feature_meta_returns_descriptor(
        self,
        temp_features_root: Path,
        configurator_service: ConfiguratorService,
        sample_feature_meta: dict
    ) -> None:
        """get_feature_meta gibt vollständigen Descriptor zurück."""
        # Arrange
        auth_dir = temp_features_root / "authenticator"
        auth_dir. mkdir(parents=True, exist_ok=True)
        (auth_dir / "meta.json").write_text(
            json. dumps(sample_feature_meta),
            encoding="utf-8"
        )

        # Act
        meta = configurator_service. get_feature_meta("authenticator")

        # Assert
        assert meta. id == "authenticator"
        assert meta.label == "Authenticator"
        assert meta.version == "1.0.0"
        assert meta.audit is not None
        assert meta.audit. must_audit is True

    def test_get_feature_meta_raises_on_missing_feature(
        self,
        configurator_service: ConfiguratorService
    ) -> None:
        """get_feature_meta wirft Exception bei fehlendem Feature."""
        # Act & Assert
        with pytest.raises(FeatureNotFoundException):
            configurator_service.get_feature_meta("nonexistent")


class TestGetAllFeatures:
    """Tests für get_all_features()."""

    def test_get_all_features_without_role_returns_all(
        self,
        temp_features_root: Path,
        configurator_service: ConfiguratorService,
        sample_feature_meta: dict
    ) -> None:
        """get_all_features ohne Rolle gibt alle Features zurück."""
        # Arrange:  2 Features mit unterschiedlicher visible_for
        # Feature 1: Für alle sichtbar (visible_for leer)
        meta1 = sample_feature_meta.copy()
        meta1["id"] = "public"
        meta1["visible_for"] = []

        public_dir = temp_features_root / "public"
        public_dir.mkdir(parents=True, exist_ok=True)
        (public_dir / "meta.json").write_text(
            json.dumps(meta1),
            encoding="utf-8"
        )

        # Feature 2: Nur für ADMIN
        meta2 = sample_feature_meta.copy()
        meta2["id"] = "admin_only"
        meta2["visible_for"] = ["ADMIN"]

        admin_dir = temp_features_root / "admin_only"
        admin_dir.mkdir(parents=True, exist_ok=True)
        (admin_dir / "meta.json").write_text(
            json.dumps(meta2),
            encoding="utf-8"
        )

        # Act
        registry = configurator_service.get_all_features()

        # Assert:   Beide Features
        assert len(registry) == 2
        feature_ids = {r.descriptor.id for r in registry}
        assert feature_ids == {"public", "admin_only"}

    def test_get_all_features_filters_by_role(
        self,
        temp_features_root: Path,
        configurator_service: ConfiguratorService,
        sample_feature_meta: dict
    ) -> None:
        """get_all_features filtert nach Rolle."""
        # Arrange: 3 Features
        # 1. Für alle
        meta1 = sample_feature_meta.copy()
        meta1["id"] = "public"
        meta1["visible_for"] = []
        public_dir = temp_features_root / "public"
        public_dir.mkdir(parents=True, exist_ok=True)
        (public_dir / "meta.json").write_text(json.dumps(meta1), encoding="utf-8")

        # 2. Nur ADMIN
        meta2 = sample_feature_meta.copy()
        meta2["id"] = "admin_only"
        meta2["visible_for"] = ["ADMIN"]
        admin_dir = temp_features_root / "admin_only"
        admin_dir.mkdir(parents=True, exist_ok=True)
        (admin_dir / "meta.json").write_text(json.dumps(meta2), encoding="utf-8")

        # 3. USER + QMB
        meta3 = sample_feature_meta.copy()
        meta3["id"] = "user_qmb"
        meta3["visible_for"] = ["USER", "QMB"]
        user_dir = temp_features_root / "user_qmb"
        user_dir.mkdir(parents=True, exist_ok=True)
        (user_dir / "meta.json").write_text(json.dumps(meta3), encoding="utf-8")

        # Act:   Als USER
        user_registry = configurator_service.get_all_features(role="USER")

        # Assert:  public + user_qmb (nicht admin_only)
        user_ids = {r.descriptor. id for r in user_registry}
        assert user_ids == {"public", "user_qmb"}

        # Act:  Als ADMIN
        admin_registry = configurator_service.get_all_features(role="ADMIN")

        # Assert: public + admin_only (nicht user_qmb, weil ADMIN nicht in visible_for)
        admin_ids = {r.descriptor.id for r in admin_registry}
        assert admin_ids == {"public", "admin_only"}

    def test_get_all_features_sorts_by_sort_order(
        self,
        temp_features_root: Path,
        configurator_service:  ConfiguratorService,
        sample_feature_meta: dict
    ) -> None:
        """get_all_features sortiert nach sort_order, dann id."""
        # Arrange: 3 Features mit unterschiedlichen sort_order
        for feature_id, sort_order in [("z", 10), ("a", 20), ("m", 10)]:
            meta = sample_feature_meta.copy()
            meta["id"] = feature_id
            meta["sort_order"] = sort_order

            feature_dir = temp_features_root / feature_id
            feature_dir.mkdir(parents=True, exist_ok=True)
            (feature_dir / "meta.json").write_text(
                json.dumps(meta),
                encoding="utf-8"
            )

        # Act
        registry = configurator_service. get_all_features()

        # Assert:  Sortierung:   sort_order aufsteigend, dann id alphabetisch
        # 10:   m, z (alphabetisch)
        # 20:  a
        feature_ids = [r.descriptor. id for r in registry]
        assert feature_ids == ["m", "z", "a"]

    def test_get_all_features_returns_registry_dtos(
        self,
        temp_features_root: Path,
        configurator_service: ConfiguratorService,
        sample_feature_meta: dict
    ) -> None:
        """get_all_features gibt FeatureRegistryDTO zurück."""
        # Arrange
        auth_dir = temp_features_root / "authenticator"
        auth_dir.mkdir(parents=True, exist_ok=True)
        (auth_dir / "meta.json").write_text(
            json.dumps(sample_feature_meta),
            encoding="utf-8"
        )

        # Act
        registry = configurator_service.get_all_features()

        # Assert
        assert len(registry) == 1
        assert isinstance(registry[0], FeatureRegistryDTO)
        assert registry[0].descriptor.id == "authenticator"
        assert registry[0].status == FeatureStatus.ACTIVE
        assert registry[0].loaded is False
        assert registry[0].error is None


class TestValidateMeta:
    """Tests für validate_meta()."""

    def test_validate_meta_returns_true_for_valid(
        self,
        temp_features_root: Path,
        configurator_service: ConfiguratorService,
        sample_feature_meta: dict
    ) -> None:
        """validate_meta gibt True für gültige meta.json."""
        # Arrange
        auth_dir = temp_features_root / "authenticator"
        auth_dir.mkdir(parents=True, exist_ok=True)
        (auth_dir / "meta.json").write_text(
            json.dumps(sample_feature_meta),
            encoding="utf-8"
        )

        # Act
        result = configurator_service.validate_meta("authenticator")

        # Assert
        assert result is True


class TestGetAppConfig:
    """Tests für get_app_config()."""

    def test_get_app_config_returns_config_dto(
        self,
        temp_features_root: Path,
        configurator_service: ConfiguratorService,
        sample_app_config: dict
    ) -> None:
        """get_app_config gibt AppConfigDTO zurück."""
        # Arrange
        config_dir = temp_features_root / "config"
        config_dir.mkdir(parents=True, exist_ok=True)
        (config_dir / "app_config.json").write_text(
            json.dumps(sample_app_config),
            encoding="utf-8"
        )

        # Act
        config = configurator_service.get_app_config()

        # Assert
        assert config.db_path == "test.db"
        assert config. default_log_level == "DEBUG"