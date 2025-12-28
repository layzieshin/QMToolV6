"""
Translation DTO Tests
=====================

Tests for translation data transfer objects.
"""

import pytest

from translation.dto.translation_dto import (
    TranslationDTO,
    TranslationSetDTO,
    CreateTranslationDTO,
    UpdateTranslationDTO,
)
from translation.dto.translation_filter_dto import TranslationFilterDTO
from translation.enum.translation_enum import SupportedLanguage, TranslationStatus


class TestTranslationDTO:
    """Tests for TranslationDTO."""

    def test_valid_creation(self):
        """Test creating valid TranslationDTO."""
        dto = TranslationDTO(
            label="core.save",
            language=SupportedLanguage.DE,
            text="Speichern",
            feature="core",
            status=TranslationStatus.COMPLETE
        )

        assert dto.label == "core.save"
        assert dto.language == SupportedLanguage.DE
        assert dto.text == "Speichern"
        assert dto.feature == "core"
        assert dto.status == TranslationStatus.COMPLETE

    def test_empty_label_raises_error(self):
        """Test that empty label raises ValueError."""
        with pytest.raises(ValueError, match="Label must be a non-empty string"):
            TranslationDTO(
                label="",
                language=SupportedLanguage.DE,
                text="Text",
                feature="core"
            )

    def test_whitespace_label_raises_error(self):
        """Test that whitespace-only label raises ValueError."""
        with pytest.raises(ValueError, match="Label cannot be whitespace-only"):
            TranslationDTO(
                label="   ",
                language=SupportedLanguage.DE,
                text="Text",
                feature="core"
            )

    def test_invalid_language_type_raises_error(self):
        """Test that non-enum language raises ValueError."""
        with pytest.raises(ValueError, match="Language must be SupportedLanguage enum"):
            TranslationDTO(
                label="test",
                language="de",  # String instead of enum
                text="Text",
                feature="core"
            )

    def test_empty_feature_raises_error(self):
        """Test that empty feature raises ValueError."""
        with pytest.raises(ValueError, match="Feature cannot be empty"):
            TranslationDTO(
                label="test",
                language=SupportedLanguage.DE,
                text="Text",
                feature=""
            )

    def test_invalid_text_type_raises_error(self):
        """Test that non-string text raises ValueError."""
        with pytest.raises(ValueError, match="Text must be a string"):
            TranslationDTO(
                label="test",
                language=SupportedLanguage.DE,
                text=123,  # int instead of string
                feature="core"
            )

    def test_is_missing_empty_text(self):
        """Test is_missing returns True for empty text."""
        dto = TranslationDTO(
            label="test",
            language=SupportedLanguage.DE,
            text="",
            feature="core",
            status=TranslationStatus.COMPLETE
        )

        assert dto.is_missing() is True

    def test_is_missing_status(self):
        """Test is_missing returns True for MISSING status."""
        dto = TranslationDTO(
            label="test",
            language=SupportedLanguage.DE,
            text="Text",
            feature="core",
            status=TranslationStatus.MISSING
        )

        assert dto.is_missing() is True

    def test_is_missing_complete(self):
        """Test is_missing returns False for complete translation."""
        dto = TranslationDTO(
            label="test",
            language=SupportedLanguage.DE,
            text="Text",
            feature="core",
            status=TranslationStatus. COMPLETE
        )

        assert dto.is_missing() is False

    def test_is_deprecated(self):
        """Test is_deprecated."""
        dto = TranslationDTO(
            label="test",
            language=SupportedLanguage.DE,
            text="Text",
            feature="core",
            status=TranslationStatus. DEPRECATED
        )

        assert dto.is_deprecated() is True

    def test_immutability(self):
        """Test that DTO is immutable (frozen)."""
        dto = TranslationDTO(
            label="test",
            language=SupportedLanguage.DE,
            text="Text",
            feature="core"
        )

        with pytest.raises(AttributeError):
            object.__setattr__(dto, "text", "New Text")


class TestTranslationSetDTO:
    """Tests for TranslationSetDTO."""

    def test_valid_creation(self):
        """Test creating valid TranslationSetDTO."""
        dto = TranslationSetDTO(
            label="core.save",
            feature="core",
            translations={
                SupportedLanguage.DE: "Speichern",
                SupportedLanguage.EN: "Save"
            }
        )

        assert dto.label == "core.save"
        assert dto.feature == "core"
        assert dto.translations[SupportedLanguage.DE] == "Speichern"
        assert dto.translations[SupportedLanguage.EN] == "Save"

    def test_empty_label_raises_error(self):
        """Test that empty label raises ValueError."""
        with pytest.raises(ValueError, match="Label must be a non-empty string"):
            TranslationSetDTO(
                label="",
                feature="core",
                translations={SupportedLanguage.DE: "Text"}
            )

    def test_invalid_translations_type_raises_error(self):
        """Test that non-dict translations raises ValueError."""
        with pytest.raises(ValueError, match="Translations must be a dict"):
            TranslationSetDTO(
                label="test",
                feature="core",
                translations=[]  # List instead of dict
            )

    def test_invalid_translation_key_raises_error(self):
        """Test that non-enum translation key raises ValueError."""
        with pytest.raises(ValueError, match="Translation keys must be SupportedLanguage enum"):
            TranslationSetDTO(
                label="test",
                feature="core",
                translations={"de": "Text"}  # String key instead of enum
            )

    def test_invalid_translation_value_raises_error(self):
        """Test that non-string translation value raises ValueError."""
        with pytest.raises(ValueError, match="Translation values must be strings"):
            TranslationSetDTO(
                label="test",
                feature="core",
                translations={SupportedLanguage.DE:  123}  # int instead of string
            )

    def test_get_missing_languages(self):
        """Test get_missing_languages."""
        dto = TranslationSetDTO(
            label="test",
            feature="core",
            translations={
                SupportedLanguage.DE: "Deutsch",
                SupportedLanguage.EN: ""  # Missing
            }
        )

        missing = dto.get_missing_languages()
        assert SupportedLanguage.EN in missing
        assert SupportedLanguage.DE not in missing

    def test_get_missing_languages_partial(self):
        """Test get_missing_languages with partial translations."""
        dto = TranslationSetDTO(
            label="test",
            feature="core",
            translations={
                SupportedLanguage.DE: "Deutsch"
                # EN completely missing
            }
        )

        missing = dto.get_missing_languages()
        assert SupportedLanguage.EN in missing

    def test_is_complete_true(self):
        """Test is_complete returns True when all languages present."""
        dto = TranslationSetDTO(
            label="test",
            feature="core",
            translations={
                SupportedLanguage.DE: "Deutsch",
                SupportedLanguage.EN: "English"
            }
        )

        assert dto.is_complete() is True

    def test_is_complete_false(self):
        """Test is_complete returns False when languages missing."""
        dto = TranslationSetDTO(
            label="test",
            feature="core",
            translations={
                SupportedLanguage.DE: "Deutsch"
            }
        )

        assert dto.is_complete() is False

    def test_get_text(self):
        """Test get_text method."""
        dto = TranslationSetDTO(
            label="test",
            feature="core",
            translations={
                SupportedLanguage.DE: "Deutsch",
                SupportedLanguage.EN: "English"
            }
        )

        assert dto.get_text(SupportedLanguage.DE) == "Deutsch"
        assert dto.get_text(SupportedLanguage.EN) == "English"

    def test_get_text_with_fallback(self):
        """Test get_text with fallback for missing language."""
        dto = TranslationSetDTO(
            label="test",
            feature="core",
            translations={
                SupportedLanguage.DE: "Deutsch"
            }
        )

        assert dto.get_text(SupportedLanguage.EN, fallback="DEFAULT") == "DEFAULT"


class TestCreateTranslationDTO:
    """Tests for CreateTranslationDTO."""

    def test_valid_creation(self):
        """Test creating valid CreateTranslationDTO."""
        dto = CreateTranslationDTO(
            label="new. key",
            feature="core",
            translations={
                SupportedLanguage.DE: "Neu",
                SupportedLanguage.EN: "New"
            }
        )

        assert dto.label == "new. key"
        assert dto.feature == "core"
        assert len(dto.translations) == 2

    def test_empty_translations_raises_error(self):
        """Test that empty translations dict raises ValueError."""
        with pytest. raises(ValueError, match="At least one translation must be provided"):
            CreateTranslationDTO(
                label="test",
                feature="core",
                translations={}
            )


class TestUpdateTranslationDTO:
    """Tests for UpdateTranslationDTO."""

    def test_valid_creation(self):
        """Test creating valid UpdateTranslationDTO."""
        dto = UpdateTranslationDTO(
            label="core.save",
            feature="core",
            language=SupportedLanguage.DE,
            text="Speichern (aktualisiert)"
        )

        assert dto.label == "core.save"
        assert dto.feature == "core"
        assert dto. language == SupportedLanguage. DE
        assert dto.text == "Speichern (aktualisiert)"

    def test_empty_text_allowed(self):
        """Test that empty text is allowed (to clear translation)."""
        dto = UpdateTranslationDTO(
            label="core.save",
            feature="core",
            language=SupportedLanguage.DE,
            text=""  # Allowed
        )

        assert dto.text == ""


class TestTranslationFilterDTO:
    """Tests for TranslationFilterDTO."""

    def test_valid_creation(self):
        """Test creating valid TranslationFilterDTO."""
        dto = TranslationFilterDTO(
            feature="core",
            language=SupportedLanguage.DE,
            status=TranslationStatus.MISSING,
            search_text="save",
            only_missing=True
        )

        assert dto.feature == "core"
        assert dto.language == SupportedLanguage.DE
        assert dto.status == TranslationStatus. MISSING
        assert dto.search_text == "save"
        assert dto.only_missing is True

    def test_all_fields_optional(self):
        """Test that all fields are optional."""
        dto = TranslationFilterDTO()

        assert dto.feature is None
        assert dto.language is None
        assert dto.status is None
        assert dto.search_text is None
        assert dto.only_missing is False

    def test_invalid_language_type_raises_error(self):
        """Test that non-enum language raises ValueError."""
        with pytest.raises(ValueError, match="Language must be SupportedLanguage enum"):
            TranslationFilterDTO(language="de")