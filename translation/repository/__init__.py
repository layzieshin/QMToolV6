# python
"""
Translation Repositories
========================

Data access layer for translation storage.

Repositories:
-------------
- TranslationRepositoryInterface: Abstract interface
- InMemoryTranslationRepository: In-memory implementation (default)
- TSVTranslationRepository: TSV file-based implementation
"""

from .translation_repository_interface import TranslationRepositoryInterface
from .translation_repository import InMemoryTranslationRepository, TSVTranslationRepository

__all__ = [
    "TranslationRepositoryInterface",
    "InMemoryTranslationRepository",
    "TSVTranslationRepository",
]
