"""
Translation Exceptions
======================

Contains all custom exceptions for the Translation feature.

Exception Hierarchy:
--------------------
TranslationException (Base)
├── TranslationNotFoundError
├── TranslationAlreadyExistsError
├── TranslationPermissionError
├── TranslationValidationError
├── TranslationLoadError
└── InvalidLanguageError
"""

from translation.exceptions.translation_exceptions import (
    TranslationException,
    TranslationNotFoundError,
    TranslationAlreadyExistsError,
    TranslationPermissionError,
    TranslationValidationError,
    TranslationLoadError,
    InvalidLanguageError,
)

__all__ = [
    "TranslationException",
    "TranslationNotFoundError",
    "TranslationAlreadyExistsError",
    "TranslationPermissionError",
    "TranslationValidationError",
    "TranslationLoadError",
    "InvalidLanguageError",
]