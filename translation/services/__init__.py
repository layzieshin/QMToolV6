"""
Translation Services
====================

Business logic layer for translation management.

Services:
---------
- TranslationServiceInterface: Service contract
- TranslationService: Core business logic implementation
- TranslationPolicy: Authorization policy

Usage:
------
    from translation.services. translation_service import TranslationService
    from translation.services.policy. translation_policy import TranslationPolicy

    policy = TranslationPolicy(user_service)
    service = TranslationService(repo, policy, audit_service, discovery_service)
"""

from translation.services.translation_service_interface import (
    TranslationServiceInterface,
)

__all__ = [
    "TranslationServiceInterface",
]