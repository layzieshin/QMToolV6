from dataclasses import dataclass
from typing import Optional
from translation.enum.language_enum import SupportedLanguage
from translation.enum.translation_status_enum import TranslationStatus


@dataclass(frozen=True)
class TranslationDTO:
    """
    Immutable DTO representing a single translation entry.

    Attributes:
        label:  Unique translation key (e.g., "core.save")
        language: Target language
        text:  Translated text
        feature: Feature this translation belongs to (e.g., "authenticator")
        status: COMPLETE, MISSING, DEPRECATED
    """
    label: str
    language: SupportedLanguage
    text: str
    feature: str
    status: TranslationStatus = TranslationStatus.COMPLETE

    def is_missing(self) -> bool:
        """Check if translation is empty or marked as MISSING."""
        return not self.text.strip() or self.status == TranslationStatus.MISSING


@dataclass(frozen=True)
class TranslationSetDTO:
    """
    Complete translation set for one label across all languages.

    Example:
        label="core.save"
        translations={
            SupportedLanguage.DE: "Speichern",
            SupportedLanguage.EN: "Save"
        }
    """
    label: str
    feature: str
    translations: dict[SupportedLanguage, str]  # {DE: "text", EN: "text"}

    def get_missing_languages(self) -> list[SupportedLanguage]:
        """Return list of languages with missing translations."""
        return [
            lang for lang in SupportedLanguage
            if lang not in self.translations or not self.translations[lang].strip()
        ]


@dataclass(frozen=True)
class CreateTranslationDTO:
    """DTO for creating new translation entry."""
    label: str
    feature: str
    translations: dict[SupportedLanguage, str]


@dataclass(frozen=True)
class UpdateTranslationDTO:
    """DTO for updating existing translation."""
    label: str
    feature: str
    language: SupportedLanguage
    text: str