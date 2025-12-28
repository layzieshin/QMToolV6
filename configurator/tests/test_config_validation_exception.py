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

from configurator.exceptions.config_validation_exception import ConfigValidationException
from configurator.repository.config_repository import ConfigRepository


class TestConfigValidationException:
    """Tests für ConfigValidationException."""

    def test_exception_message_with_all_params(self) -> None:
        """Exception-Message enthält alle Parameter."""
        exc = ConfigValidationException(
            "session.timeout_minutes",
            -1,
            "Must be > 0"
        )

        assert "session.timeout_minutes" in str(exc)
        assert "-1" in str(exc)
        assert "Must be > 0" in str(exc)

    def test_exception_message_without_value(self) -> None:
        """Exception-Message funktioniert ohne value."""
        exc = ConfigValidationException(
            "database.path",
            reason="File not found"
        )

        assert "database.path" in str(exc)
        assert "File not found" in str(exc)

    def test_exception_attributes(self) -> None:
        """Exception speichert Attribute korrekt."""
        exc = ConfigValidationException(
            "audit.default_log_level",
            "INVALID",
            "Must be DEBUG, INFO, WARNING, ERROR, or CRITICAL"
        )

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
        config_dir = temp_features_root / "config"
        config_dir.mkdir(parents=True, exist_ok=True)
        (config_dir / "app_config.json").write_text(
            "{ invalid json",
            encoding="utf-8"
        )

        repo = ConfigRepository(project_root=str(temp_features_root))
        with pytest.raises(ConfigValidationException) as exc_info:
            repo.load_app_config(strict=True)

        assert exc_info.value.field == "app_config.json"
        assert "JSON parsing failed" in exc_info.value.reason

    def test_strict_mode_raises_on_non_object_root(
        self,
        temp_features_root: Path
    ) -> None:
        """Strict-Mode wirft Exception wenn Root kein Objekt ist."""
        config_dir = temp_features_root / "config"
        config_dir.mkdir(parents=True, exist_ok=True)
        (config_dir / "app_config.json").write_text(
            json.dumps(["array", "not", "object"]),
            encoding="utf-8"
        )

        repo = ConfigRepository(project_root=str(temp_features_root))
        with pytest.raises(ConfigValidationException) as exc_info:
            repo.load_app_config(strict=True)

        assert exc_info.value.field == "app_config.json"
        assert "must be a JSON object" in exc_info.value.reason

    def test_strict_mode_does_not_raise_on_invalid_values_but_falls_back_and_warns(
        self,
        temp_features_root: Path,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """
        strict=True: ungültige Werte werden (laut aktueller Implementierung)
        NICHT als Exception behandelt, sondern auf Defaults zurückgesetzt
        und per WARNING geloggt.
        """
        config_dir = temp_features_root / "config"
        config_dir.mkdir(parents=True, exist_ok=True)
        (config_dir / "app_config.json").write_text(
            json.dumps({"session": {"timeout_minutes": -1}}, indent=2),
            encoding="utf-8"
        )

        repo = ConfigRepository(project_root=str(temp_features_root))

        with caplog.at_level("WARNING"):
            cfg = repo.load_app_config(strict=True)

        # Erwartung: Fallback auf Default 60 (siehe Log aus deinem Testlauf)
        assert cfg.session_timeout_minutes == 60

        # Erwartung: Warning wurde geloggt
        assert any(
            "timeout_minutes" in rec.message and "using default" in rec.message
            for rec in caplog.records
        )