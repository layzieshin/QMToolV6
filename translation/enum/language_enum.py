from enum import Enum


class SupportedLanguage(Enum):
    """
    ISO 639-1 language codes for supported languages.

    Extend this enum when adding new languages:
        FR = "fr"  # French
        ES = "es"  # Spanish
    """
    DE = "de"  # German
    EN = "en"  # English

    @classmethod
    def from_string(cls, lang_code: str) -> "SupportedLanguage":
        """
        Convert string to enum (case-insensitive).

        Raises:
            ValueError: If language not supported
        """
        try:
            return cls[lang_code.upper()]
        except KeyError:
            raise ValueError(
                f"Unsupported language:  {lang_code}. "
                f"Supported:  {[e.value for e in cls]}"
            )

    @classmethod
    def all_codes(cls) -> list[str]:
        """Return all language codes as strings."""
        return [lang.value for lang in cls]


class TranslationStatus(Enum):
    """Status of a translation entry."""
    COMPLETE = "complete"  # Translation exists and is valid
    MISSING = "missing"  # Translation missing or empty
    DEPRECATED = "deprecated"  # Old key, should be removed