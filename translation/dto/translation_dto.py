"""
Translation DTOs
================

Core data transfer objects for translation data.

DTOs:
-----
- TranslationDTO: Single translation entry
- TranslationSetDTO: Complete translation set (all languages)
- CreateTranslationDTO: Input for creating translations
- UpdateTranslationDTO: Input for updating translations
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from translation.enum.translation_enum import SupportedLanguage, TranslationStatus


def _validate_non_empty_string(value: object, field_name: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string, got {type(value).__name__}")
    if not value.strip():
        raise ValueError(f"{field_name} cannot be empty or whitespace-only")
    return value


@dataclass(frozen=True, slots=True)
class TranslationDTO:
    """
    Represents a single translation entry for one label + one language.

    NOTE:
    - frozen=True and slots=True are crucial for immutability tests:
      setting attributes must raise AttributeError.
    """

    label: str
    language: SupportedLanguage
    text: str
    feature: str
    status: TranslationStatus

    def __post_init__(self) -> None:
        _validate_non_empty_string(self.label, "Label")
        _validate_non_empty_string(self.feature, "Feature")

        if not isinstance(self.language, SupportedLanguage):
            raise ValueError(
                f"Language must be SupportedLanguage enum, got {type(self.language).__name__}"
            )
        if not isinstance(self.status, TranslationStatus):
            raise ValueError(
                f"Status must be TranslationStatus enum, got {type(self.status).__name__}"
            )
        if not isinstance(self.text, str):
            raise ValueError(f"Text must be a string, got {type(self.text).__name__}")


@dataclass(frozen=True, slots=True)
class TranslationSetDTO:
    """
    Represents a translation set (label + translations across multiple languages).
    """

    label: str
    feature: str
    translations: Dict[SupportedLanguage, str]

    def __post_init__(self) -> None:
        _validate_non_empty_string(self.label, "Label")
        _validate_non_empty_string(self.feature, "Feature")

        if not isinstance(self.translations, dict):
            raise ValueError(
                f"Translations must be a dict, got {type(self.translations).__name__}"
            )

        for k, v in self.translations.items():
            if not isinstance(k, SupportedLanguage):
                raise ValueError(
                    f"Translations keys must be SupportedLanguage, got {type(k).__name__}"
                )
            if not isinstance(v, str):
                raise ValueError(
                    f"Translations values must be str, got {type(v).__name__}"
                )

    def get_missing_languages(self) -> List[SupportedLanguage]:
        """
        Returns languages that are missing (empty or whitespace-only).
        """
        missing: List[SupportedLanguage] = []
        for lang in SupportedLanguage:
            val = self.translations.get(lang, "")
            if not isinstance(val, str) or not val.strip():
                missing.append(lang)
        return missing

    def is_complete(self) -> bool:
        """
        True if all SupportedLanguage have non-empty text.
        """
        return len(self.get_missing_languages()) == 0


@dataclass(frozen=True, slots=True)
class CreateTranslationDTO:
    """
    Input DTO for creating a new translation set.
    """

    label: str
    feature: str
    translations: Dict[SupportedLanguage, str]

    def __post_init__(self) -> None:
        _validate_non_empty_string(self.label, "Label")
        _validate_non_empty_string(self.feature, "Feature")
        if not isinstance(self.translations, dict):
            raise ValueError("Translations must be a dict")


@dataclass(frozen=True, slots=True)
class UpdateTranslationDTO:
    """
    Input DTO for updating one translation entry in an existing set.
    """

    label: str
    feature: str
    language: SupportedLanguage
    text: str

    def __post_init__(self) -> None:
        _validate_non_empty_string(self.label, "Label")
        _validate_non_empty_string(self.feature, "Feature")
        if not isinstance(self.language, SupportedLanguage):
            raise ValueError("Language must be SupportedLanguage")
        if not isinstance(self.text, str):
            raise ValueError("Text must be a string")
