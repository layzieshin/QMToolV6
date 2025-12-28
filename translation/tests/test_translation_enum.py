"""
Translation Enums
=================

Enums for the Translation feature.

Rules:
- Keep error messages stable because tests (and sometimes logs) depend on them.
- from_string must be case-insensitive.
"""

from __future__ import annotations

from enum import Enum


class SupportedLanguage(Enum):
    """
    ISO 639-1 language codes for supported languages.

    Extend this enum when adding new languages.
    """

    DE = "de"  # German
    EN = "en"  # English

    @classmethod
    def from_string(cls, lang_code: str) -> "SupportedLanguage":
        """
        Convert a string to SupportedLanguage (case-insensitive).

        Raises:
            ValueError: If the language is not supported.

        Important:
            The error message prefix is intentionally stable for unit tests:
            "Unsupported language:␠␠<code>"
        """
        if not isinstance(lang_code, str):
            raise TypeError("lang_code must be a string")

        try:
            return cls[lang_code.strip().upper()]
        except KeyError:
            # NOTE: Two spaces after ':' are required by an existing test expectation.
            raise ValueError(
                f"Unsupported language:  {lang_code}"
            )


    @classmethod
    def all_codes(cls) -> list[str]:
        """Return all language codes as strings."""
        return [lang.value for lang in cls]

    def __str__(self) -> str:
        """String representation returns the ISO code."""
        return self.value


class TranslationStatus(Enum):
    """Status of a translation entry."""
    COMPLETE = "complete"
    MISSING = "missing"
    DEPRECATED = "deprecated"

    def __str__(self) -> str:
        """String representation returns the status value."""
        return self.value
