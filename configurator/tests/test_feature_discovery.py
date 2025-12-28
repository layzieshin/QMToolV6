"""
Unit Tests für Feature Discovery.

Testet das Scannen und Laden von Features aus meta.json.

Author: QMToolV6 Development Team
Version: 1.0.0
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from configurator.exceptions. feature_not_found_exception import FeatureNotFoundException
from configurator.exceptions.invalid_meta_exception import InvalidMetaException
from configurator.repository.feature_repository import FeatureRepository


class TestFeatureDiscovery:
    """Tests für Feature-Discovery."""

    def test_discover_all_finds_valid_features(
        self,
        temp_features_root: Path,
        sample_feature_meta: dict
    ) -> None:
        """Discovery findet alle gültigen Features."""
        # Arrange:   3 Features erstellen
        for feature_id in ["authenticator", "user_management", "audittrail"]:
            meta = sample_feature_meta.copy()
            meta["id"] = feature_id
            meta["label"] = feature_id. title()

            feature_dir = temp_features_root / feature_id
            feature_dir.mkdir(parents=True, exist_ok=True)
            (feature_dir / "meta. json").write_text(
                json.dumps(meta),
                encoding="utf-8"
            )

        # Act
        repo = FeatureRepository(features_root=str(temp_features_root))
        features = repo. discover_all()

        # Assert
        assert len(features) == 3
        feature_ids = sorted([f.id for f in features])
        assert feature_ids == ["audittrail", "authenticator", "user_management"]

    def test_discover_ignores_configured_folders(
        self,
        temp_features_root: Path,
        sample_feature_meta: dict
    ) -> None:
        """Discovery ignoriert IGNORE_FOLDERS."""
        # Arrange:  1 gültiges Feature + 1 ignorierter Ordner
        # Gültiges Feature
        auth_meta = sample_feature_meta.copy()
        auth_dir = temp_features_root / "authenticator"
        auth_dir.mkdir(parents=True, exist_ok=True)
        (auth_dir / "meta.json").write_text(
            json.dumps(auth_meta),
            encoding="utf-8"
        )

        # Ignorierter Ordner (shared)
        shared_meta = sample_feature_meta.copy()
        shared_meta["id"] = "shared"
        shared_dir = temp_features_root / "shared"
        shared_dir.mkdir(parents=True, exist_ok=True)
        (shared_dir / "meta.json").write_text(
            json.dumps(shared_meta),
            encoding="utf-8"
        )

        # Act
        repo = FeatureRepository(features_root=str(temp_features_root))
        features = repo.discover_all()

        # Assert:  Nur authenticator gefunden, shared ignoriert
        assert len(features) == 1
        assert features[0].id == "authenticator"

    def test_discover_skips_folders_without_meta_json(
        self,
        temp_features_root: Path
    ) -> None:
        """Discovery überspringt Ordner ohne meta.json."""
        # Arrange:  Ordner ohne meta.json
        (temp_features_root / "no_meta").mkdir(parents=True, exist_ok=True)

        # Act
        repo = FeatureRepository(features_root=str(temp_features_root))
        features = repo.discover_all()

        # Assert
        assert len(features) == 0

    def test_discover_raises_on_invalid_meta(
        self,
        temp_features_root: Path
    ) -> None:
        """Discovery wirft Exception bei ungültiger meta.json."""
        # Arrange:  Ungültige JSON
        feature_dir = temp_features_root / "broken"
        feature_dir.mkdir(parents=True, exist_ok=True)
        (feature_dir / "meta.json").write_text(
            "{ invalid json",
            encoding="utf-8"
        )

        # Act & Assert
        repo = FeatureRepository(features_root=str(temp_features_root))
        with pytest.raises(InvalidMetaException) as exc_info:
            repo.discover_all()

        assert "JSON-Parsing fehlgeschlagen" in str(exc_info.value)

    def test_discover_caches_descriptors(
        self,
        temp_features_root: Path,
        sample_feature_meta: dict
    ) -> None:
        """Cache wird für get_by_id() verwendet."""
        # Arrange
        auth_dir = temp_features_root / "authenticator"
        auth_dir.mkdir(parents=True, exist_ok=True)
        (auth_dir / "meta. json").write_text(
            json.dumps(sample_feature_meta),
            encoding="utf-8"
        )

        repo = FeatureRepository(features_root=str(temp_features_root))

        # Act:  Erstes Discovery füllt Cache
        features_1 = repo.discover_all()
        assert features_1[0].version == "1.0.0"

        # meta.json ändern
        modified_meta = sample_feature_meta. copy()
        modified_meta["version"] = "2.0.0"
        (auth_dir / "meta.json").write_text(
            json.dumps(modified_meta),
            encoding="utf-8"
        )

        # get_by_id() nutzt Cache
        descriptor_cached = repo.get_by_id("authenticator")

        # Assert: get_by_id() gibt gecachte Version zurück
        assert descriptor_cached.version == "1.0.0"  # Cached!

        # discover_all() liest neu von Disk und aktualisiert Cache
        features_2 = repo.discover_all()
        assert features_2[0].version == "2.0.0"  # Neu gelesen!

        # Jetzt ist Cache aktualisiert
        descriptor_new = repo.get_by_id("authenticator")
        assert descriptor_new.version == "2.0.0"  # Cache aktualisiert


class TestGetFeatureById:
    """Tests für get_by_id()."""

    def test_get_by_id_returns_cached_descriptor(
        self,
        temp_features_root: Path,
        sample_feature_meta: dict
    ) -> None:
        """get_by_id nutzt Cache nach Discovery."""
        # Arrange
        auth_dir = temp_features_root / "authenticator"
        auth_dir.mkdir(parents=True, exist_ok=True)
        (auth_dir / "meta.json").write_text(
            json.dumps(sample_feature_meta),
            encoding="utf-8"
        )

        repo = FeatureRepository(features_root=str(temp_features_root))
        repo.discover_all()  # Füllt Cache

        # Act
        descriptor = repo.get_by_id("authenticator")

        # Assert
        assert descriptor.id == "authenticator"
        assert descriptor.version == "1.0.0"

    def test_get_by_id_loads_from_disk_if_not_cached(
        self,
        temp_features_root: Path,
        sample_feature_meta: dict
    ) -> None:
        """get_by_id lädt von Disk wenn nicht im Cache."""
        # Arrange
        auth_dir = temp_features_root / "authenticator"
        auth_dir.mkdir(parents=True, exist_ok=True)
        (auth_dir / "meta.json").write_text(
            json.dumps(sample_feature_meta),
            encoding="utf-8"
        )

        repo = FeatureRepository(features_root=str(temp_features_root))
        # KEIN discover_all() → Cache leer

        # Act
        descriptor = repo.get_by_id("authenticator")

        # Assert
        assert descriptor.id == "authenticator"
        assert descriptor. version == "1.0.0"

    def test_get_by_id_raises_on_missing_feature(
        self,
        temp_features_root: Path
    ) -> None:
        """get_by_id wirft Exception wenn Feature nicht existiert."""
        # Arrange
        repo = FeatureRepository(features_root=str(temp_features_root))

        # Act & Assert
        with pytest.raises(FeatureNotFoundException) as exc_info:
            repo.get_by_id("nonexistent")

        assert exc_info.value.feature_id == "nonexistent"


class TestIdConvention:
    """Tests für id == Ordnername-Konvention."""

    def test_id_must_equal_folder_name(
        self,
        temp_features_root: Path,
        sample_feature_meta: dict
    ) -> None:
        """meta.json id muss Ordnername entsprechen."""
        # Arrange:   id != Ordnername
        meta = sample_feature_meta.copy()
        meta["id"] = "wrong_id"  # Ordner heißt "user_management"

        feature_dir = temp_features_root / "user_management"
        feature_dir.mkdir(parents=True, exist_ok=True)
        (feature_dir / "meta.json").write_text(
            json.dumps(meta),
            encoding="utf-8"
        )

        # Act & Assert
        repo = FeatureRepository(features_root=str(temp_features_root))
        with pytest.raises(InvalidMetaException) as exc_info:
            repo.discover_all()

        assert "id` muss dem Ordnernamen entsprechen" in str(exc_info.value)
        assert exc_info.value.feature_id == "user_management"

    def test_id_convention_case_sensitive(
        self,
        temp_features_root: Path,
        sample_feature_meta: dict
    ) -> None:
        """id-Konvention ist case-sensitive."""
        # Arrange: Case mismatch
        meta = sample_feature_meta.copy()
        meta["id"] = "Authenticator"  # Ordner heißt "authenticator"

        feature_dir = temp_features_root / "authenticator"
        feature_dir.mkdir(parents=True, exist_ok=True)
        (feature_dir / "meta.json").write_text(
            json.dumps(meta),
            encoding="utf-8"
        )

        # Act & Assert
        repo = FeatureRepository(features_root=str(temp_features_root))
        with pytest.raises(InvalidMetaException) as exc_info:
            repo.discover_all()

        assert "id` muss dem Ordnernamen entsprechen" in str(exc_info.value)