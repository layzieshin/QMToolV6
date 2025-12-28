"""
Translation Enums
=================

All enumerations for the Translation feature.

Enums:
------
- SupportedLanguage: ISO 639-1 language codes
- TranslationStatus: Translation entry status
"""

from enum import Enum


class SupportedLanguage(Enum):
    """
    ISO 639-1 language codes for supported languages.

    Attributes:
        DE:  German
        EN: English

    Usage:
    ------
        >>> lang = SupportedLanguage.DE
        >>> lang.value
        'de'

        >>> SupportedLanguage.from_string("en")
        <SupportedLanguage.EN:  'en'>

    Extension:
    ----------
    To add new languages:
        FR = "fr"  # French
        ES = "es"  # Spanish
    """
    DE = "de"
    EN = "en"

    @classmethod
    def from_string(cls, lang_code: str) -> "SupportedLanguage":
        """
        Convert string to SupportedLanguage enum (case-insensitive).

        Args:
            lang_code: Language code string (e.g., "de", "EN", "De")

        Returns:
            SupportedLanguage enum member

        Raises:
            ValueError: If language code not supported

        Example:
        --------
            >>> SupportedLanguage.from_string("de")
            <SupportedLanguage.DE: 'de'>

            >>> SupportedLanguage.from_string("fr")
            ValueError:  Unsupported language:  fr.  Supported: ['de', 'en']
        """
        try:
            return cls[lang_code.upper()]
        except KeyError:
            supported = [lang.value for lang in cls]
            raise ValueError(
                f"Unsupported language: {lang_code}.  Supported: {supported}"
            )

    @classmethod
    def all_codes(cls) -> list[str]:
        """
        Return all language codes as list of strings.

        Returns:
            List of language code strings

        Example:
        --------
            >>> SupportedLanguage. all_codes()
            ['de', 'en']
        """
        return [lang.value for lang in cls]

    def __str__(self) -> str:
        """String representation (returns code)."""
        return self.value


class TranslationStatus(Enum):
    """
    Status of a translation entry.

    Attributes:
        COMPLETE: Translation exists and is valid
        MISSING: Translation missing or empty
        DEPRECATED: Old key, should be removed/replaced

    Usage:
    ------
        >>> status = TranslationStatus.COMPLETE
        >>> status. value
        'complete'

        >>> TranslationStatus. MISSING
        <TranslationStatus.MISSING:  'missing'>
    """
    COMPLETE = "complete"
    MISSING = "missing"
    DEPRECATED = "deprecated"

    def __str__(self) -> str:
        """String representation (returns value)."""
        return self.value