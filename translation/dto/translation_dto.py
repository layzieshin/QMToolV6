"""
Translation DTOs
================

Core data transfer objects for translation data.

DTOs:
-----
- TranslationDTO: Single translation entry
- TranslationSetDTO:  Complete translation set (all languages)
- CreateTranslationDTO: Input for creating translations
- UpdateTranslationDTO:  Input for updating translations
"""

from dataclasses import dataclass
from typing import Dict

from translation.enum.translation_enum import SupportedLanguage, TranslationStatus


@dataclass(frozen=True)
class TranslationDTO:
    """
    Immutable DTO representing a single translation entry.

    Attributes:
        label:  Unique translation key (e.g., "core.save", "auth.login")
        language: Target language (DE, EN, ...)
        text: Translated text (can be empty for MISSING status)
        feature: Feature this translation belongs to (e.g., "authenticator")
        status: Translation status (COMPLETE, MISSING, DEPRECATED)

    Validation:
        - label:  non-empty string, no whitespace-only
        - language: must be SupportedLanguage enum
        - text: must be string (can be empty)
        - feature: non-empty string
        - status:  must be TranslationStatus enum

    Example:
    --------
        >>> dto = TranslationDTO(
        ...     label="core.save",
        ...     language=SupportedLanguage.DE,
        ...     text="Speichern",
        ...     feature="core",
        ...     status=TranslationStatus.COMPLETE
        ... )
        >>> dto.is_missing()
        False
    """
    label: str
    language: SupportedLanguage
    text: str
    feature:  str
    status: TranslationStatus = TranslationStatus.COMPLETE

    def __post_init__(self):
        """
        Validate DTO fields after initialization.

        Raises:
            ValueError: If any field fails validation
        """
        # Label validation
        if not self.label or not isinstance(self.label, str):
            raise ValueError("Label must be a non-empty string")
        if not self.label.strip():
            raise ValueError("Label cannot be whitespace-only")

        # Language validation
        if not isinstance(self.language, SupportedLanguage):
            raise ValueError(
                f"Language must be SupportedLanguage enum, got {type(self.language).__name__}"
            )

        # Feature validation
        if not isinstance(self.feature, str):
            raise ValueError(f"Feature must be a string, got {type(self.feature).__name__}")
        if not self.feature.strip():
            raise ValueError("Feature cannot be empty or whitespace-only")

        # Text validation (CAN be empty for MISSING status)
        if not isinstance(self.text, str):
            raise ValueError(f"Text must be a string, got {type(self.text).__name__}")

        # Status validation
        if not isinstance(self.status, TranslationStatus):
            raise ValueError(
                f"Status must be TranslationStatus enum, got {type(self.status).__name__}"
            )

    def is_missing(self) -> bool:
        """
        Check if translation is missing or empty.

        Returns:
            True if text is empty OR status is MISSING

        Example:
        --------
            >>> dto = TranslationDTO(... , text="", status=TranslationStatus.COMPLETE)
            >>> dto.is_missing()
            True
        """
        return not self.text. strip() or self.status == TranslationStatus.MISSING

    def is_deprecated(self) -> bool:
        """
        Check if translation is marked as deprecated.

        Returns:
            True if status is DEPRECATED
        """
        return self.status == TranslationStatus.DEPRECATED


@dataclass(frozen=True)
class TranslationSetDTO:
    """
    Complete translation set for one label across all languages.

    Attributes:
        label: Unique translation key
        feature: Feature name
        translations: Dict mapping language to text {DE: "text", EN: "text"}

    Validation:
        - label: non-empty string
        - feature: non-empty string
        - translations: dict with SupportedLanguage keys

    Example:
    --------
        >>> dto = TranslationSetDTO(
        ...     label="core.save",
        ...     feature="core",
        ...     translations={
        ...         SupportedLanguage.DE: "Speichern",
        ...         SupportedLanguage.EN:  "Save"
        ...     }
        ... )
        >>> dto.get_missing_languages()
        []
    """
    label: str
    feature: str
    translations: Dict[SupportedLanguage, str]

    def __post_init__(self):
        """
        Validate DTO fields after initialization.

        Raises:
            ValueError:  If any field fails validation
        """
        # Label validation
        if not self.label or not isinstance(self.label, str):
            raise ValueError("Label must be a non-empty string")
        if not self.label.strip():
            raise ValueError("Label cannot be whitespace-only")

        # Feature validation
        if not isinstance(self.feature, str):
            raise ValueError(f"Feature must be a string, got {type(self.feature).__name__}")
        if not self.feature.strip():
            raise ValueError("Feature cannot be empty or whitespace-only")

        # Translations validation
        if not isinstance(self.translations, dict):
            raise ValueError(
                f"Translations must be a dict, got {type(self.translations).__name__}"
            )

        # Validate all keys are SupportedLanguage
        for lang, text in self.translations.items():
            if not isinstance(lang, SupportedLanguage):
                raise ValueError(
                    f"Translation keys must be SupportedLanguage enum, got {type(lang).__name__}"
                )
            if not isinstance(text, str):
                raise ValueError(
                    f"Translation values must be strings, got {type(text).__name__} for {lang}"
                )

    def get_missing_languages(self) -> list[SupportedLanguage]:
        """
        Return list of languages with missing/empty translations.

        Returns:
            List of SupportedLanguage enums for missing translations

        Example:
        --------
            >>> dto = TranslationSetDTO(
            ...     label="test",
            ...     feature="core",
            ...     translations={SupportedLanguage.DE: "Text", SupportedLanguage.EN:  ""}
            ... )
            >>> dto.get_missing_languages()
            [<SupportedLanguage.EN: 'en'>]
        """
        missing = []
        for lang in SupportedLanguage:
            text = self.translations.get(lang, "")
            if not text.strip():
                missing.append(lang)
        return missing

    def is_complete(self) -> bool:
        """
        Check if all languages have translations.

        Returns:
            True if no missing languages
        """
        return len(self.get_missing_languages()) == 0

    def get_text(self, language: SupportedLanguage, fallback: str = "") -> str:
        """
        Get translation text for specific language with fallback.

        Args:
            language: Target language
            fallback: Default text if translation missing

        Returns:
            Translation text or fallback
        """
        return self.translations.get(language, fallback)


@dataclass(frozen=True)
class CreateTranslationDTO:
    """
    DTO for creating a new translation set.

    Attributes:
        label:  Unique translation key
        feature: Feature name
        translations: Dict with at least one language

    Validation:
        - Same as TranslationSetDTO
        - At least one translation must be provided

    Example:
    --------
        >>> dto = CreateTranslationDTO(
        ...     label="new.key",
        ...     feature="core",
        ...     translations={
        ...         SupportedLanguage.DE: "Neuer Text",
        ...         SupportedLanguage.EN: "New Text"
        ...     }
        ... )
    """
    label: str
    feature: str
    translations: Dict[SupportedLanguage, str]

    def __post_init__(self):
        """
        Validate DTO fields.

        Raises:
            ValueError: If validation fails
        """
        # Label validation
        if not self.label or not isinstance(self.label, str):
            raise ValueError("Label must be a non-empty string")
        if not self.label. strip():
            raise ValueError("Label cannot be whitespace-only")

        # Feature validation
        if not isinstance(self.feature, str):
            raise ValueError(f"Feature must be a string, got {type(self.feature).__name__}")
        if not self. feature.strip():
            raise ValueError("Feature cannot be empty or whitespace-only")

        # Translations validation
        if not isinstance(self.translations, dict):
            raise ValueError(
                f"Translations must be a dict, got {type(self.translations).__name__}"
            )

        if not self.translations:
            raise ValueError("At least one translation must be provided")

        # Validate keys and values
        for lang, text in self.translations.items():
            if not isinstance(lang, SupportedLanguage):
                raise ValueError(
                    f"Translation keys must be SupportedLanguage enum, got {type(lang).__name__}"
                )
            if not isinstance(text, str):
                raise ValueError(
                    f"Translation values must be strings, got {type(text).__name__}"
                )


@dataclass(frozen=True)
class UpdateTranslationDTO:
    """
    DTO for updating a single translation.

    Attributes:
        label: Translation key to update
        feature: Feature name
        language: Language to update
        text: New translation text

    Validation:
        - All fields non-empty
        - language must be SupportedLanguage enum

    Example:
    --------
        >>> dto = UpdateTranslationDTO(
        ...     label="core.save",
        ...      feature="core",
        ...      language=SupportedLanguage.DE,
        ...     text="Speichern (aktualisiert)"
        ... )
    """
    label: str
    feature: str
    language: SupportedLanguage
    text: str

    def __post_init__(self):
        """
        Validate DTO fields.

        Raises:
            ValueError: If validation fails
        """
        # Label validation
        if not self.label or not isinstance(self.label, str):
            raise ValueError("Label must be a non-empty string")
        if not self.label.strip():
            raise ValueError("Label cannot be whitespace-only")

        # Feature validation
        if not isinstance(self.feature, str):
            raise ValueError(f"Feature must be a string, got {type(self.feature).__name__}")
        if not self.feature.strip():
            raise ValueError("Feature cannot be empty or whitespace-only")

        # Language validation
        if not isinstance(self.language, SupportedLanguage):
            raise ValueError(
                f"Language must be SupportedLanguage enum, got {type(self.language).__name__}"
            )

        # Text validation (CAN be empty to clear translation)
        if not isinstance(self.text, str):
            raise ValueError(f"Text must be a string, got {type(self.text).__name__}")