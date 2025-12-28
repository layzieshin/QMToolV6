"""
Translation Service Tests
=========================

Tests for translation service business logic.
"""

import pytest

from translation.dto.translation_dto import CreateTranslationDTO, UpdateTranslationDTO
from translation.dto.translation_filter_dto import TranslationFilterDTO
from translation.enum.translation_enum import SupportedLanguage, TranslationStatus
from translation.exceptions.translation_exceptions import (
    TranslationNotFoundError,
    TranslationAlreadyExistsError,
    TranslationPermissionError,
)


class TestTranslationService:
    """Tests for TranslationService."""

    def test_get_existing_translation(self, translation_service):
        """Test getting existing translation text."""
        text = translation_service.get("core.save", SupportedLanguage.DE, "core")

        assert text == "Speichern"

    def test_get_missing_translation_with_fallback(self, translation_service):
        """Test getting missing translation returns label as fallback."""
        text = translation_service.get("nonexistent. key", SupportedLanguage. DE, "core", fallback_to_label=True)

        assert text == "nonexistent.key"

    def test_get_missing_translation_without_fallback(self, translation_service):
        """Test getting missing translation returns empty string without fallback."""
        text = translation_service.get("nonexistent.key", SupportedLanguage.DE, "core", fallback_to_label=False)

        assert text == ""

    def test_get_missing_translation_logs_audit(self, translation_service, mock_audit_service):
        """Test that missing translation logs audit entry."""
        translation_service.get("missing.key", SupportedLanguage.EN, "test")

        # Should have logged missing translation
        assert mock_audit_service.log. called
        call_details = mock_audit_service.log.call_args[1]["details"]
        assert call_details["event"] == "missing_translation"
        assert call_details["label"] == "missing.key"

    def test_get_missing_translation_logs_once(self, translation_service, mock_audit_service):
        """Test that same missing translation is only logged once."""
        # Call twice with same key
        translation_service. get("missing.key", SupportedLanguage.EN, "test")
        translation_service.get("missing.key", SupportedLanguage.EN, "test")

        # Should only log once
        assert mock_audit_service.log.call_count == 1

    def test_get_translation_dto(self, translation_service):
        """Test getting full TranslationDTO."""
        dto = translation_service.get_translation("core.save", SupportedLanguage.DE, "core")

        assert dto is not None
        assert dto.label == "core. save"
        assert dto.text == "Speichern"
        assert dto.status == TranslationStatus.COMPLETE

    def test_get_translation_set(self, translation_service):
        """Test getting translation set."""
        set_dto = translation_service. get_translation_set("core. save", "core")

        assert set_dto is not None
        assert set_dto.label == "core.save"
        assert set_dto.translations[SupportedLanguage.DE] == "Speichern"
        assert set_dto.translations[SupportedLanguage.EN] == "Save"

    def test_query_translations_by_feature(self, translation_service):
        """Test querying translations by feature."""
        filter_dto = TranslationFilterDTO(feature="core")
        results = translation_service.query_translations(filter_dto)

        assert len(results) == 3
        assert all(r.feature == "core" for r in results)

    def test_query_translations_only_missing(self, translation_service):
        """Test querying only missing translations."""
        filter_dto = TranslationFilterDTO(feature="core", only_missing=True)
        results = translation_service.query_translations(filter_dto)

        assert len(results) == 1
        assert results[0].label == "core.missing"

    def test_query_translations_by_search_text(self, translation_service):
        """Test querying translations by search text."""
        filter_dto = TranslationFilterDTO(search_text="save")
        results = translation_service.query_translations(filter_dto)

        assert len(results) >= 1
        assert any("save" in r.label. lower() for r in results)

    def test_create_translation_success(self, translation_service, mock_audit_service):
        """Test creating new translation."""
        dto = CreateTranslationDTO(
            label="new.key",
            feature="core",
            translations={
                SupportedLanguage.DE: "Neu",
                SupportedLanguage. EN: "New"
            }
        )

        result = translation_service.create_translation(dto, actor_id=1)  # Admin

        assert result. label == "new.key"
        assert mock_audit_service.log.called

    def test_create_translation_permission_denied(self, translation_service):
        """Test creating translation without permission raises error."""
        dto = CreateTranslationDTO(
            label="new.key",
            feature="core",
            translations={SupportedLanguage.DE: "Neu"}
        )

        with pytest.raises(TranslationPermissionError):
            translation_service.create_translation(dto, actor_id=3)  # Regular user

    def test_create_translation_already_exists_raises_error(self, translation_service):
        """Test creating duplicate translation raises error."""
        dto = CreateTranslationDTO(
            label="core.save",  # Already exists
            feature="core",
            translations={SupportedLanguage.DE: "Dupe"}
        )

        with pytest.raises(TranslationAlreadyExistsError):
            translation_service.create_translation(dto, actor_id=1)

    def test_update_translation_success(self, translation_service, mock_audit_service):
        """Test updating translation."""
        dto = UpdateTranslationDTO(
            label="core.save",
            feature="core",
            language=SupportedLanguage.DE,
            text="Aktualisiert"
        )

        result = translation_service.update_translation(dto, actor_id=1)  # Admin

        assert result.text == "Aktualisiert"
        assert mock_audit_service.log.called

    def test_update_translation_permission_denied(self, translation_service):
        """Test updating translation without permission raises error."""
        dto = UpdateTranslationDTO(
            label="core.save",
            feature="core",
            language=SupportedLanguage.DE,
            text="Neu"
        )

        with pytest.raises(TranslationPermissionError):
            translation_service.update_translation(dto, actor_id=3)  # Regular user

    def test_update_translation_not_found_raises_error(self, translation_service):
        """Test updating non-existent translation raises error."""
        dto = UpdateTranslationDTO(
            label="nonexistent",
            feature="core",
            language=SupportedLanguage. DE,
            text="Text"
        )

        with pytest.raises(TranslationNotFoundError):
            translation_service.update_translation(dto, actor_id=1)

    def test_delete_translation_success(self, translation_service, mock_audit_service):
        """Test deleting translation."""
        translation_service.delete_translation("core.save", "core", actor_id=1)  # Admin

        # Should be deleted
        assert translation_service.get_translation_set("core.save", "core") is None

        # Should have logged with CRITICAL severity
        assert mock_audit_service.log.called
        call_details = mock_audit_service. log.call_args[1]
        assert call_details["severity"] == "CRITICAL"

    def test_delete_translation_permission_denied_for_qmb(self, translation_service):
        """Test that QMB cannot delete (ADMIN only)."""
        with pytest.raises(TranslationPermissionError):
            translation_service.delete_translation("core.save", "core", actor_id=2)  # QMB

    def test_delete_translation_not_found_raises_error(self, translation_service):
        """Test deleting non-existent translation raises error."""
        with pytest.raises(TranslationNotFoundError):
            translation_service.delete_translation("nonexistent", "core", actor_id=1)

    def test_get_missing_for_feature(self, translation_service):
        """Test getting missing translations for feature."""
        missing = translation_service.get_missing_for_feature("core")

        assert len(missing) == 1
        assert missing[0].label == "core.missing"

    def test_get_coverage(self, translation_service):
        """Test getting coverage statistics."""
        coverage = translation_service.get_coverage("core")

        assert SupportedLanguage.DE in coverage
        assert SupportedLanguage.EN in coverage
        assert coverage[SupportedLanguage.DE] == 1.0  # All DE present

    def test_get_all_features(self, translation_service):
        """Test getting all loaded features."""
        features = translation_service.get_all_features()

        assert "core" in features

    def test_load_all_features(self, translation_service, mock_feature_structure, feature_discovery_service):
        """Test auto-loading all features."""
        # Reinitialize service with mock feature structure
        from translation.services.translation_service import TranslationService
        from translation.repository.translation_repository import InMemoryTranslationRepository

        repo = InMemoryTranslationRepository()
        discovery = feature_discovery_service

        service = TranslationService(
            repository=repo,
            policy=translation_service._policy,
            audit_service=translation_service._audit,
            discovery_service=discovery
        )

        loaded = service.load_all_features()

        assert "authenticator" in loaded
        assert "user_management" in loaded
        assert loaded["authenticator"] == 1  # 1 translation loaded
        assert loaded["user_management"] == 1

    def test_export_feature_tsv(self, translation_service, tmp_path):
        """Test exporting feature as TSV."""
        output_path = tmp_path / "export.tsv"

        translation_service.export_feature("core", str(output_path), format="tsv")

        assert output_path.exists()
        content = output_path.read_text(encoding="utf-8")
        assert "core.save" in content

    def test_export_feature_json(self, translation_service, tmp_path):
        """Test exporting feature as JSON."""
        output_path = tmp_path / "export.json"

        translation_service.export_feature("core", str(output_path), format="json")

        assert output_path.exists()

        import json
        data = json.loads(output_path.read_text(encoding="utf-8"))
        assert data["feature"] == "core"
        assert len(data["translations"]) == 3

    def test_export_feature_csv(self, translation_service, tmp_path):
        """Test exporting feature as CSV."""
        output_path = tmp_path / "export.csv"

        translation_service.export_feature("core", str(output_path), format="csv")

        assert output_path.exists()
        content = output_path.read_text(encoding="utf-8")
        assert "core.save" in content

    def test_export_feature_invalid_format_raises_error(self, translation_service, tmp_path):
        """Test exporting with invalid format raises error."""
        with pytest.raises(ValueError, match="Unsupported export format"):
            translation_service.export_feature("core", str(tmp_path / "export.xml"), format="xml")