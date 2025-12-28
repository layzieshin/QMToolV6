"""
Translation Exceptions
======================

Custom exceptions for Translation feature operations.

All exceptions inherit from TranslationException base class
to allow catch-all error handling.

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


class TranslationException(Exception):
    """
    Base exception for all Translation feature errors.

    Allows catch-all error handling:
        try:
            service.create_translation(...)
        except TranslationException as e:
            # Handle any translation error
            pass
    """
    pass


class TranslationNotFoundError(TranslationException):
    """
    Raised when a translation or translation set is not found.

    Scenarios:
    ----------
    - get_translation() with non-existent label
    - update_translation() for missing entry
    - delete_translation_set() for non-existent set

    Example:
    --------
        >>> service.get_translation_set("nonexistent. key", "core")
        TranslationNotFoundError: Translation set not found: core. nonexistent.key
    """
    pass


class TranslationAlreadyExistsError(TranslationException):
    """
    Raised when attempting to create a duplicate translation.

    Scenarios:
    ----------
    - create_translation() with existing label/feature combination

    Example:
    --------
        >>> service.create_translation(CreateTranslationDTO(...))
        TranslationAlreadyExistsError: Translation already exists: core.save
    """
    pass


class TranslationPermissionError(TranslationException):
    """
    Raised when actor lacks permission for a translation operation.

    Scenarios:
    ----------
    - Non-Admin/QMB attempts to create translation
    - Non-Admin/QMB attempts to update translation
    - Non-Admin attempts to delete translation

    Example:
    --------
        >>> service.create_translation(dto, actor_id=regular_user_id)
        TranslationPermissionError: Actor 123 lacks permission to create translations
    """
    pass


class TranslationValidationError(TranslationException):
    """
    Raised when translation data fails validation.

    Scenarios:
    ----------
    - Empty label in DTO
    - Invalid language code
    - Malformed translation data

    Example:
    --------
        >>> TranslationDTO(label="", language=SupportedLanguage.DE, ...)
        TranslationValidationError: Label must be a non-empty string
    """
    pass


class TranslationLoadError(TranslationException):
    """
    Raised when loading translations from TSV fails.

    Scenarios:
    ----------
    - TSV file not found
    - Invalid TSV format (missing columns, wrong delimiter)
    - Unsupported language in header
    - File read/write errors

    Example:
    --------
        >>> repo.load_feature_tsv("core", "/invalid/path.tsv")
        TranslationLoadError: TSV file not found: /invalid/path.tsv
    """
    pass


class InvalidLanguageError(TranslationException):
    """
    Raised when an unsupported language code is provided.

    Scenarios:
    ----------
    - SupportedLanguage.from_string() with invalid code
    - TSV header contains unsupported language

    Example:
    --------
        >>> SupportedLanguage.from_string("fr")
        InvalidLanguageError: Unsupported language:  fr. Supported: ['de', 'en']
    """
    pass