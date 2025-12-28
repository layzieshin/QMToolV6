"""
Translation Repositories
========================

Data access layer for translation storage.

Repositories:
-------------
- TranslationRepositoryInterface: Abstract interface
- InMemoryTranslationRepository: In-memory implementation (default)
- TSVTranslationRepository: TSV file-based implementation

Usage:
------
    from translation.repository. translation_repository import InMemoryTranslationRepository

    repo = InMemoryTranslationRepository()
    repo.load_feature_tsv("core", "core/labels.tsv")
"""

from translation.repository.translation_repository_interface import (
    TranslationRepositoryInterface,
)
from translation.repository.translation_repository import (
    InMemoryTranslationRepository,
    TSVTranslationRepository,
)

__all__ = [
    "TranslationRepositoryInterface",
    "InMemoryTranslationRepository",
    "TSVTranslationRepository",
]