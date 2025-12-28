"""
Unit Tests für App-Config-Loading.

Testet das Laden von config/app_config.json.

Author: QMToolV6 Development Team
Version: 1.1.0
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from configurator.exceptions.config_validation_exception import ConfigValidationException
from configurator. repository.config_repository import ConfigRepository


class TestAppConfigDefaults:
    """Tests für Default-Werte."""

    def test_load_app_config_uses_defaults_when_file_missing(
        self,
        temp_features_root: Path
    ) -> None:
        """Verwendet Defaults wenn app_config.json fehlt."""
        # Arrange: Keine config/app_config.json
        repo = ConfigRepository(project_root=str(temp_features_root))

        # Act
        config = repo.load_app_config()

        # Assert: Alle Defaults
        assert config.db_path == "qmtool.db"
        assert config.default_log_level == "INFO"
        assert config.default_retention_days == 365
        assert config.features_root == "."
        assert config.data_dir == "./data"
        assert config.temp_dir == "./temp"
        assert config.session_timeout_minutes == 60
        assert config.max_failed_logins == 5
        assert config.app_name == "QMToolV6"
        assert config.app_version == "0.1.0"


class TestAppConfigOverrides:
    """Tests für Config-Overrides."""

    def test_load_app_config_applies_overrides(
        self,
        temp_features_root:  Path,
        sample_app_config: dict
    ) -> None:
        """Lädt Overrides aus app_config.json."""
        # Arrange:  config/app_config.json erstellen
        config_dir = temp_features_root / "config"
        config_dir.mkdir(parents=True, exist_ok=True)
        (config_dir / "app_config.json").write_text(
            json.dumps(sample_app_config),
            encoding="utf-8"
        )

        # Act
        repo = ConfigRepository(project_root=str(temp_features_root))
        config = repo.load_app_config()

        # Assert: Overrides angewendet
        assert config.app_name == "QMToolV6"
        assert config.app_version == "1.0.0"
        assert config.db_path == "test.db"
        assert config. default_log_level == "DEBUG"
        assert config.default_retention_days == 90
        assert config.session_timeout_minutes == 30
        assert config.max_failed_logins == 3
        assert config.features_root == "."
        assert config. data_dir == "./test_data"
        assert config. temp_dir == "./test_temp"

    def test_load_app_config_partial_overrides(
        self,
        temp_features_root:  Path
    ) -> None:
        """Partielle Overrides verwenden Defaults für fehlende Werte."""
        # Arrange:   Nur database. path überschreiben
        partial_config = {
            "database": {
                "path": "custom.db"
            }
        }

        config_dir = temp_features_root / "config"
        config_dir.mkdir(parents=True, exist_ok=True)
        (config_dir / "app_config.json").write_text(
            json.dumps(partial_config),
            encoding="utf-8"
        )

        # Act
        repo = ConfigRepository(project_root=str(temp_features_root))
        config = repo.load_app_config()

        # Assert: db_path überschrieben, Rest Defaults
        assert config.db_path == "custom.db"
        assert config.default_log_level == "INFO"  # Default
        assert config.session_timeout_minutes == 60  # Default


class TestAppConfigValidation:
    """Tests für Config-Validierung."""

    def test_invalid_json_uses_defaults_non_strict(
        self,
        temp_features_root: Path
    ) -> None:
        """Ungültiges JSON führt zu Defaults (nicht-strict)."""
        # Arrange: Ungültiges JSON
        config_dir = temp_features_root / "config"
        config_dir.mkdir(parents=True, exist_ok=True)
        (config_dir / "app_config.json").write_text(
            "{ invalid json",
            encoding="utf-8"
        )

        # Act
        repo = ConfigRepository(project_root=str(temp_features_root))
        config = repo.load_app_config(strict=False)

        # Assert: Defaults verwendet
        assert config.db_path == "qmtool.db"

    def test_invalid_json_raises_exception_strict(
        self,
        temp_features_root: Path
    ) -> None:
        """Ungültiges JSON wirft Exception (strict)."""
        # Arrange: Ungültiges JSON
        config_dir = temp_features_root / "config"
        config_dir.mkdir(parents=True, exist_ok=True)
        (config_dir / "app_config.json").write_text(
            "{ invalid",
            encoding="utf-8"
        )

        # Act & Assert
        repo = ConfigRepository(project_root=str(temp_features_root))
        with pytest.raises(ConfigValidationException):
            repo.load_app_config(strict=True)

    def test_non_object_root_uses_defaults(
        self,
        temp_features_root: Path
    ) -> None:
        """Nicht-Objekt-Root führt zu Defaults."""
        # Arrange: JSON ist Array statt Objekt
        config_dir = temp_features_root / "config"
        config_dir.mkdir(parents=True, exist_ok=True)
        (config_dir / "app_config.json").write_text(
            json.dumps(["array", "not", "object"]),
            encoding="utf-8"
        )

        # Act
        repo = ConfigRepository(project_root=str(temp_features_root))
        config = repo.load_app_config()

        # Assert: Defaults verwendet
        assert config.db_path == "qmtool.db"

    def test_invalid_int_values_use_defaults(
        self,
        temp_features_root: Path
    ) -> None:
        """Ungültige Int-Werte verwenden Defaults."""
        # Arrange: timeout_minutes ist String statt Int
        invalid_config = {
            "session": {
                "timeout_minutes": "not_a_number",
                "max_failed_logins": 3
            }
        }

        config_dir = temp_features_root / "config"
        config_dir.mkdir(parents=True, exist_ok=True)
        (config_dir / "app_config.json").write_text(
            json.dumps(invalid_config),
            encoding="utf-8"
        )

        # Act
        repo = ConfigRepository(project_root=str(temp_features_root))
        config = repo.load_app_config()

        # Assert: timeout_minutes verwendet Default, max_failed_logins OK
        assert config.session_timeout_minutes == 60  # Default
        assert config.max_failed_logins == 3  # Aus config

    def test_negative_values_use_defaults(
        self,
        temp_features_root: Path
    ) -> None:
        """Negative Werte verwenden Defaults (min_value Check)."""
        # Arrange: retention_days < 0
        invalid_config = {
            "audit": {
                "default_retention_days": -100
            }
        }

        config_dir = temp_features_root / "config"
        config_dir.mkdir(parents=True, exist_ok=True)
        (config_dir / "app_config.json").write_text(
            json.dumps(invalid_config),
            encoding="utf-8"
        )

        # Act
        repo = ConfigRepository(project_root=str(temp_features_root))
        config = repo.load_app_config()

        # Assert: Verwendet Default wegen min_value=1 Validierung
        assert config.default_retention_days == 365  # Default


class TestAppConfigDTOMethods:
    """Tests für AppConfigDTO Helper-Methoden."""

    def test_get_db_path_returns_path_object(
        self,
        temp_features_root: Path,
        sample_app_config: dict
    ) -> None:
        """get_db_path() gibt Path-Objekt zurück."""
        # Arrange
        config_dir = temp_features_root / "config"
        config_dir.mkdir(parents=True, exist_ok=True)
        (config_dir / "app_config.json").write_text(
            json.dumps(sample_app_config),
            encoding="utf-8"
        )

        repo = ConfigRepository(project_root=str(temp_features_root))
        config = repo.load_app_config()

        # Act
        db_path = config.get_db_path()

        # Assert
        assert isinstance(db_path, Path)
        assert str(db_path) == "test.db"

    def test_get_data_dir_returns_path_object(
        self,
        temp_features_root: Path,
        sample_app_config: dict
    ) -> None:
        """get_data_dir() gibt Path-Objekt zurück."""
        # Arrange
        config_dir = temp_features_root / "config"
        config_dir.mkdir(parents=True, exist_ok=True)
        (config_dir / "app_config.json").write_text(
            json.dumps(sample_app_config),
            encoding="utf-8"
        )

        repo = ConfigRepository(project_root=str(temp_features_root))
        config = repo. load_app_config()

        # Act
        data_dir = config.get_data_dir()

        # Assert
        assert isinstance(data_dir, Path)
        # Path normalisiert automatisch ". /" weg
        assert data_dir.name == "test_data"

    def test_validate_raises_on_invalid_values(self) -> None:
        """validate() wirft ValueError bei ungültigen Werten."""
        # Arrange & Act & Assert
        from configurator.dto.app_config_dto import AppConfigDTO

        # session_timeout_minutes <= 0
        with pytest.raises(ValueError, match="session_timeout_minutes must be > 0"):
            config = AppConfigDTO(session_timeout_minutes=0)
            config.validate()

        # max_failed_logins <= 0
        with pytest.raises(ValueError, match="max_failed_logins must be > 0"):
            config = AppConfigDTO(max_failed_logins=-1)
            config.validate()

        # retention_days <= 0
        with pytest.raises(ValueError, match="default_retention_days must be > 0"):
            config = AppConfigDTO(default_retention_days=0)
            config.validate()

        # invalid log_level
        with pytest.raises(ValueError, match="default_log_level must be one of"):
            config = AppConfigDTO(default_log_level="INVALID")
            config.validate()