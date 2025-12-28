"""
Translation Enum Tests
======================

Tests for translation enumerations.
"""

import pytest

from translation.enum. translation_enum import SupportedLanguage, TranslationStatus


class TestSupportedLanguage:
    """Tests for SupportedLanguage enum."""

    def test_enum_values(self):
        """Test that enum values are correct."""
        assert SupportedLanguage.DE.value == "de"
        assert SupportedLanguage.EN.value == "en"

    def test_from_string_valid(self):
        """Test from_string with valid language codes."""
        assert SupportedLanguage.from_string("de") == SupportedLanguage.DE
        assert SupportedLanguage.from_string("en") == SupportedLanguage.EN

        # Case-insensitive
        assert SupportedLanguage.from_string("DE") == SupportedLanguage.DE
        assert SupportedLanguage.from_string("En") == SupportedLanguage. EN

    def test_from_string_invalid(self):
        """Test from_string with invalid language code."""
        with pytest.raises(ValueError, match="Unsupported language:  fr"):
            SupportedLanguage.from_string("fr")

        with pytest.raises(ValueError, match="Unsupported language: es"):
            SupportedLanguage.from_string("es")

    def test_all_codes(self):
        """Test all_codes returns all language codes."""
        codes = SupportedLanguage.all_codes()
        assert "de" in codes
        assert "en" in codes
        assert len(codes) == 2

    def test_str_representation(self):
        """Test string representation returns value."""
        assert str(SupportedLanguage.DE) == "de"
        assert str(SupportedLanguage.EN) == "en"


class TestTranslationStatus:
    """Tests for TranslationStatus enum."""

    def test_enum_values(self):
        """Test that enum values are correct."""
        assert TranslationStatus.COMPLETE.value == "complete"
        assert TranslationStatus.MISSING.value == "missing"
        assert TranslationStatus.DEPRECATED.value == "deprecated"

    def test_str_representation(self):
        """Test string representation returns value."""
        assert str(TranslationStatus. COMPLETE) == "complete"
        assert str(TranslationStatus.MISSING) == "missing"
        assert str(TranslationStatus.DEPRECATED) == "deprecated"