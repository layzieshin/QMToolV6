"""
Translation Feature
===================

Provides multi-language support for QMToolV6.

Features:
- TSV-based translation storage (feature-specific labels. tsv files)
- Auto-discovery of feature translations
- Policy-based translation management (Admin/QMB can edit)
- Full audit trail integration
- Missing translation detection and logging
- Export/import capabilities

Usage:
------
    from translation. services.translation_service import TranslationService
    from translation.repository.translation_repository import InMemoryTranslationRepository
    from translation.enum.translation_enum import SupportedLanguage

    # Setup
    repo = InMemoryTranslationRepository()
    service = TranslationService(repo, policy, audit_service, discovery_service)

    # Get translation
    text = service.get("core.save", SupportedLanguage.DE, "core")
    # Returns: "Speichern"

Public API:
-----------
- TranslationService:  Core business logic
- TranslationServiceInterface: Service contract
- TranslationDTO:  Immutable translation data
- SupportedLanguage: Language enum (DE, EN)
- TranslationException: Base exception

Author: QMToolV6 Team
Version: 1.0.0
"""

from translation.dto.translation_dto import (
    TranslationDTO,
    TranslationSetDTO,
    CreateTranslationDTO,
    UpdateTranslationDTO,
)
from translation.enum.translation_enum import (
    SupportedLanguage,
    TranslationStatus,
)
from translation.exceptions.translation_exceptions import (
    TranslationException,
    TranslationNotFoundError,
    TranslationAlreadyExistsError,
    TranslationPermissionError,
    TranslationValidationError,
    TranslationLoadError,
    InvalidLanguageError,
)
from translation.services.translation_service_interface import (
    TranslationServiceInterface,
)

__all__ = [
    # DTOs
    "TranslationDTO",
    "TranslationSetDTO",
    "CreateTranslationDTO",
    "UpdateTranslationDTO",
    # Enums
    "SupportedLanguage",
    "TranslationStatus",
    # Exceptions
    "TranslationException",
    "TranslationNotFoundError",
    "TranslationAlreadyExistsError",
    "TranslationPermissionError",
    "TranslationValidationError",
    "TranslationLoadError",
    "InvalidLanguageError",
    # Service Interface
    "TranslationServiceInterface",
]

__version__ = "1.0.0"