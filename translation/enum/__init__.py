"""
Translation Enums
=================

Contains all enumerations used in the Translation feature.

Enums:
------
- SupportedLanguage:  ISO 639-1 language codes (DE, EN)
- TranslationStatus: Status of translation entries (COMPLETE, MISSING, DEPRECATED)
"""

from translation.enum.translation_enum import (
    SupportedLanguage,
    TranslationStatus,
)

__all__ = [
    "SupportedLanguage",
    "TranslationStatus",
]