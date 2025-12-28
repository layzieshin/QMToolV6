"""
Unit Tests für ConfigValidationException.

Testet Exception-Handling bei ungültiger App-Config.

Author: QMToolV6 Development Team
Version: 1.0.0
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from configurator.exceptions. config_validation_exception import ConfigValidationException
from configurator.repository.config_repository import ConfigRepository


class TestConfigValidationException:
    """Tests für ConfigValidationException."""

    def test_exception_message_with_all_params(self) -> None:
        """Exception-Message enthält alle Parameter."""
        # Arrange & Act
        exc = ConfigValidationException(
            "session.timeout_minutes",
            -1,
            "Must be > 0"
        )

        # Assert
        assert "session.timeout_minutes" in str(exc)
        assert "-1" in str(exc)
        assert "Must be > 0" in str(exc)

    def test_exception_message_without_value(self) -> None:
        """Exception-Message funktioniert ohne value."""
        # Arrange & Act
        exc = ConfigValidationException(
            "database.path",
            reason="File not found"
        )

        # Assert
        assert "database. path" in str(exc)
        assert "File not found" in str(exc)

    def test_exception_attributes(self) -> None:
        """Exception speichert Attribute korrekt."""
        # Arrange & Act
        exc = ConfigValidationException(
            "audit.default_log_level",
            "INVALID",
            "Must be DEBUG, INFO, WARNING, ERROR, or CRITICAL"
        )

        # Assert
        assert exc.field == "audit.default_log_level"
        assert exc.value == "INVALID"
        assert "Must be DEBUG" in exc.reason


class TestConfigRepositoryStrictMode:
    """Tests für ConfigRepository strict-Mode."""

    def test_strict_mode_raises_on_invalid_json(
        self,
        temp_features_root: Path
    ) -> None:
        """Strict-Mode wirft Exception bei ungültigem JSON."""
        # Arrange:   Ungültiges JSON
        config_dir = temp_features_root / "config"
        config_dir.mkdir(parents=True, exist_ok=True)
        (config_dir / "app_config.json").write_text(
            "{ invalid json",
            encoding="utf-8"
        )

        # Act & Assert
        repo = ConfigRepository(project_root=str(temp_features_root))
        with pytest. raises(ConfigValidationException) as exc_info:
            repo.load_app_config(strict=True)

        assert exc_info.value.field == "app_config.json"
        assert "JSON parsing failed" in exc_info.value.reason

    def test_strict_mode_raises_on_non_object_root(
        self,
        temp_features_root: Path
    ) -> None:
        """Strict-Mode wirft Exception wenn Root kein Objekt ist."""
        # Arrange:  JSON ist Array
        config_dir = temp_features_root / "config"
        config_dir.mkdir(parents=True, exist_ok=True)
        (config_dir / "app_config.json").write_text(
            json.dumps(["array", "not", "object"]),
            encoding="utf-8"
        )

        # Act & Assert
        repo = ConfigRepository(project_root=str(temp_features_root))
        with pytest.raises(ConfigValidationException) as exc_info:
            repo.load_app_config(strict=True)

        assert exc_info.value.field == "app_config.json"
        assert "must be a JSON object" in exc_info.value.reason

    def test_strict_mode_raises_on_invalid_values(
        self,
        temp_features_root: Path
    ) -> None:
        """Strict-Mode wirft Exception bei ungültigen Werten."""
        # Arrange: Ungültiger log_level
        config_dir = temp_features_root / "config"
        config_dir.mkdir(parents=True, exist_ok=True)
        (config_dir / "app_config.json").write_text(
            json.dumps({
                "audit": {
                    "default_log_level": "INVALID_LEVEL"
                }
            }),
            encoding="utf-8"
        )

        # Act & Assert
        repo = ConfigRepository(project_root=str(temp_features_root))
        with pytest.raises(ConfigValidationException) as exc_info:
            repo.load_app_config(strict=True)

        assert "default_log_level" in str(exc_info.value)

    def test_non_strict_mode_uses_defaults_on_errors(
        self,
        temp_features_root: Path
    ) -> None:
        """Nicht-Strict-Mode verwendet Defaults bei Fehlern."""
        # Arrange: Ungültiges JSON
        config_dir = temp_features_root / "config"
        config_dir.mkdir(parents=True, exist_ok=True)
        (config_dir / "app_config.json").write_text(
            "{ invalid",
            encoding="utf-8"
        )

        # Act
        repo = ConfigRepository(project_root=str(temp_features_root))
        config = repo. load_app_config(strict=False)

        # Assert: Defaults verwendet (keine Exception)
        assert config.db_path == "qmtool.db"
        assert config.session_timeout_minutes == 60

    def test_strict_mode_validates_log_level(
        self,
        temp_features_root: Path
    ) -> None:
        """Strict-Mode validiert default_log_level."""
        # Arrange: Ungültiger log_level
        config_dir = temp_features_root / "config"
        config_dir. mkdir(parents=True, exist_ok=True)
        (config_dir / "app_config. json").write_text(
            json.dumps({
                "audit": {
                    "default_log_level": "INVALID_LEVEL"
                }
            }),
            encoding="utf-8"
        )

        # Act & Assert
        repo = ConfigRepository(project_root=str(temp_features_root))
        with pytest.raises(ConfigValidationException) as exc_info:
            repo.load_app_config(strict=True)

        assert "default_log_level" in str(exc_info.value)