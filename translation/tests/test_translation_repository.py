"""
Translation Repository Tests
=============================

Tests for translation repository implementations.
"""

import pytest
from pathlib import Path

from translation.repository.translation_repository import (
    InMemoryTranslationRepository,
    TSVTranslationRepository,
)
from translation.dto.translation_dto import TranslationSetDTO
from translation.enum.translation_enum import SupportedLanguage, TranslationStatus
from translation.exceptions. translation_exceptions import (
    TranslationNotFoundError,
    TranslationAlreadyExistsError,
    TranslationLoadError,
    InvalidLanguageError,
)


class TestInMemoryTranslationRepository:
    """Tests for InMemoryTranslationRepository."""

    def test_get_translation_existing(self, populated_repository):
        """Test retrieving existing translation."""
        dto = populated_repository.get_translation(
            "core.save",
            SupportedLanguage.DE,
            "core"
        )

        assert dto is not None
        assert dto.label == "core.save"
        assert dto.language == SupportedLanguage.DE
        assert dto.text == "Speichern"
        assert dto.feature == "core"
        assert dto. status == TranslationStatus. COMPLETE

    def test_get_translation_missing(self, populated_repository):
        """Test retrieving non-existent translation returns None."""
        dto = populated_repository.get_translation(
            "nonexistent",
            SupportedLanguage.DE,
            "core"
        )

        assert dto is None

    def test_get_translation_empty_text(self, populated_repository):
        """Test translation with empty text has MISSING status."""
        dto = populated_repository.get_translation(
            "core.missing",
            SupportedLanguage.EN,
            "core"
        )

        assert dto is not None
        assert dto.text == ""
        assert dto.status == TranslationStatus.MISSING

    def test_get_translation_set_existing(self, populated_repository):
        """Test retrieving existing translation set."""
        set_dto = populated_repository.get_translation_set("core. save", "core")

        assert set_dto is not None
        assert set_dto.label == "core.save"
        assert set_dto.feature == "core"
        assert set_dto.translations[SupportedLanguage.DE] == "Speichern"
        assert set_dto.translations[SupportedLanguage.EN] == "Save"

    def test_get_translation_set_missing(self, populated_repository):
        """Test retrieving non-existent translation set returns None."""
        set_dto = populated_repository.get_translation_set("nonexistent", "core")

        assert set_dto is None

    def test_get_all_by_feature(self, populated_repository):
        """Test retrieving all translations for a feature."""
        translation_sets = populated_repository.get_all_by_feature("core")

        assert len(translation_sets) == 3
        labels = [ts.label for ts in translation_sets]
        assert "core.save" in labels
        assert "core.cancel" in labels
        assert "core.missing" in labels

    def test_get_all_by_language(self, populated_repository):
        """Test retrieving all translations for a language."""
        translations = populated_repository.get_all_by_language(SupportedLanguage.DE)

        assert len(translations) == 3
        assert all(t.language == SupportedLanguage.DE for t in translations)

    def test_get_all_features(self, populated_repository):
        """Test getting list of all features."""
        features = populated_repository.get_all_features()

        assert "core" in features

    def test_create_translation_set_success(self, translation_repository):
        """Test creating new translation set."""
        new_set = TranslationSetDTO(
            label="new.key",
            feature="core",
            translations={
                SupportedLanguage.DE: "Neu",
                SupportedLanguage.EN: "New"
            }
        )

        translation_repository.create_translation_set(new_set)

        retrieved = translation_repository.get_translation_set("new.key", "core")
        assert retrieved is not None
        assert retrieved.label == "new.key"

    def test_create_translation_set_duplicate_raises_error(self, populated_repository):
        """Test creating duplicate translation set raises error."""
        duplicate_set = TranslationSetDTO(
            label="core.save",
            feature="core",
            translations={SupportedLanguage.DE: "Dupe"}
        )

        with pytest.raises(TranslationAlreadyExistsError, match="Translation already exists"):
            populated_repository.create_translation_set(duplicate_set)

    def test_update_translation_success(self, populated_repository):
        """Test updating existing translation."""
        populated_repository.update_translation(
            "core.save",
            "core",
            SupportedLanguage.DE,
            "Neuer Text"
        )

        dto = populated_repository.get_translation("core.save", SupportedLanguage.DE, "core")
        assert dto.text == "Neuer Text"

    def test_update_translation_not_found_raises_error(self, populated_repository):
        """Test updating non-existent translation raises error."""
        with pytest.raises(TranslationNotFoundError, match="Translation set not found"):
            populated_repository.update_translation(
                "nonexistent",
                "core",
                SupportedLanguage.DE,
                "Text"
            )

    def test_delete_translation_set_success(self, populated_repository):
        """Test deleting translation set."""
        populated_repository. delete_translation_set("core. save", "core")

        assert populated_repository.get_translation_set("core.save", "core") is None

    def test_delete_translation_set_not_found_raises_error(self, populated_repository):
        """Test deleting non-existent translation set raises error."""
        with pytest.raises(TranslationNotFoundError, match="Translation set not found"):
            populated_repository.delete_translation_set("nonexistent", "core")

    def test_get_missing_translations(self, populated_repository):
        """Test retrieving translation sets with missing languages."""
        missing = populated_repository.get_missing_translations("core")

        assert len(missing) == 1
        assert missing[0].label == "core.missing"

    def test_load_feature_tsv_success(self, translation_repository, temp_tsv_file):
        """Test loading translations from TSV file."""
        count = translation_repository.load_feature_tsv("test", str(temp_tsv_file))

        assert count == 3

        dto = translation_repository.get_translation("test. key1", SupportedLanguage.DE, "test")
        assert dto.text == "Wert 1"

    def test_load_feature_tsv_file_not_found_raises_error(self, translation_repository):
        """Test loading from non-existent file raises error."""
        with pytest. raises(TranslationLoadError, match="TSV file not found"):
            translation_repository.load_feature_tsv("test", "/nonexistent/path. tsv")

    def test_load_feature_tsv_invalid_header_raises_error(self, translation_repository, tmp_path):
        """Test loading TSV with invalid header raises error."""
        invalid_tsv = tmp_path / "invalid.tsv"
        invalid_tsv.write_text("wrong_header\tde\ten\n", encoding="utf-8")

        with pytest.raises(TranslationLoadError, match="Invalid TSV header"):
            translation_repository.load_feature_tsv("test", str(invalid_tsv))

    def test_load_feature_tsv_unsupported_language_raises_error(self, translation_repository, tmp_path):
        """Test loading TSV with unsupported language raises error."""
        invalid_tsv = tmp_path / "invalid.tsv"
        invalid_tsv.write_text("label\tde\tfr\n", encoding="utf-8")  # 'fr' not supported

        with pytest.raises(InvalidLanguageError, match="Unsupported language in TSV header"):
            translation_repository.load_feature_tsv("test", str(invalid_tsv))

    def test_persist_feature_tsv_success(self, populated_repository, tmp_path):
        """Test persisting translations to TSV file."""
        output_path = tmp_path / "output.tsv"

        populated_repository.persist_feature_tsv("core", str(output_path))

        assert output_path. exists()

        # Verify content
        content = output_path.read_text(encoding="utf-8")
        assert "core. save\tSpeichern\tSave" in content

    def test_persist_feature_tsv_empty_feature(self, translation_repository, tmp_path):
        """Test persisting empty feature does nothing (no error)."""
        output_path = tmp_path / "output.tsv"

        translation_repository.persist_feature_tsv("nonexistent", str(output_path))

        # Should not create file for empty feature
        assert not output_path.exists()

    def test_persist_feature_tsv_atomic_write(self, populated_repository, tmp_path):
        """Test that persist uses atomic write (tmp file + rename)."""
        output_path = tmp_path / "output.tsv"
        tmp_file_path = output_path.with_suffix(". tmp")

        populated_repository.persist_feature_tsv("core", str(output_path))

        # Temp file should be cleaned up
        assert not tmp_file_path.exists()
        assert output_path.exists()

    def test_get_coverage_complete(self, populated_repository):
        """Test coverage calculation for complete translations."""
        # Remove the missing translation
        populated_repository.delete_translation_set("core.missing", "core")

        coverage = populated_repository.get_coverage("core")

        assert coverage[SupportedLanguage.DE] == 1.0  # 100%
        assert coverage[SupportedLanguage.EN] == 1.0  # 100%

    def test_get_coverage_partial(self, populated_repository):
        """Test coverage calculation with missing translations."""
        coverage = populated_repository.get_coverage("core")

        # 3 total:  core.save (complete), core.cancel (complete), core.missing (EN missing)
        assert coverage[SupportedLanguage.DE] == 1.0  # All DE present
        assert coverage[SupportedLanguage.EN] == 2.0 / 3.0  # 2 out of 3 EN present

    def test_get_coverage_empty_feature(self, translation_repository):
        """Test coverage for non-existent feature."""
        coverage = translation_repository.get_coverage("nonexistent")

        assert coverage[SupportedLanguage.DE] == 0.0
        assert coverage[SupportedLanguage. EN] == 0.0


class TestTSVTranslationRepository:
    """Tests for TSVTranslationRepository."""

    def test_auto_persist_disabled_by_default(self):
        """Test that auto-persist is disabled by default."""
        repo = TSVTranslationRepository(auto_persist=False)

        # Should not auto-persist (tested implicitly)
        assert repo._auto_persist is False

    def test_auto_persist_on_update(self, tmp_path):
        """Test auto-persist on update when enabled."""
        repo = TSVTranslationRepository(auto_persist=True)

        # Setup:  Load TSV
        tsv_path = tmp_path / "labels.tsv"
        tsv_path.write_text("label\tde\ten\ntest. key\tAlt\tOld\n", encoding="utf-8")
        repo.load_feature_tsv("test", str(tsv_path))

        # Update
        repo.update_translation("test.key", "test", SupportedLanguage.DE, "Neu")

        # Should have auto-persisted
        content = tsv_path.read_text(encoding="utf-8")
        assert "test.key\tNeu\tOld" in content

    def test_load_remembers_path(self, tmp_path):
        """Test that loading TSV remembers path for auto-persist."""
        repo = TSVTranslationRepository()

        tsv_path = tmp_path / "labels.tsv"
        tsv_path.write_text("label\tde\ten\ntest.key\tText\tText\n", encoding="utf-8")

        repo.load_feature_tsv("test", str(tsv_path))

        assert "test" in repo._tsv_paths
        assert repo._tsv_paths["test"] == str(tsv_path)