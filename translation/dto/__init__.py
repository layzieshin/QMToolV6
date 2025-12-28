"""
Translation DTOs
================

Data Transfer Objects for the Translation feature.

DTOs:
-----
- TranslationDTO: Single translation (label + language + text)
- TranslationSetDTO: Complete set of translations (all languages for one label)
- CreateTranslationDTO: Input for creating new translation set
- UpdateTranslationDTO:  Input for updating single translation
- TranslationFilterDTO: Filter criteria for queries

All DTOs are immutable (frozen=True) and validated in __post_init__.
"""

from translation.dto.translation_dto import (
    TranslationDTO,
    TranslationSetDTO,
    CreateTranslationDTO,
    UpdateTranslationDTO,
)
from translation.dto.translation_filter_dto import (
    TranslationFilterDTO,
)

__all__ = [
    "TranslationDTO",
    "TranslationSetDTO",
    "CreateTranslationDTO",
    "UpdateTranslationDTO",
    "TranslationFilterDTO",
]