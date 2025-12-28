from abc import ABC, abstractmethod
from typing import Optional
from translation.dto.translation_dto import TranslationDTO, TranslationSetDTO
from translation.enum.language_enum import SupportedLanguage


class TranslationRepositoryInterface(ABC):
    """
    Abstract repository for translation storage.

    Implementation can be:
    - TSV-based (current V4 system)
    - Database-based (future SQL storage)
    - Hybrid (TSV for development, DB for production)
    """

    @abstractmethod
    def get_translation(
            self,
            label: str,
            language: SupportedLanguage,
            feature: str
    ) -> Optional[TranslationDTO]:
        """
        Retrieve single translation.

        Returns:
            TranslationDTO if found, None otherwise
        """
        pass

    @abstractmethod
    def get_translation_set(self, label: str, feature: str) -> Optional[TranslationSetDTO]:
        """Get all language variants for a label."""
        pass

    @abstractmethod
    def get_all_by_feature(self, feature: str) -> list[TranslationSetDTO]:
        """Get all translation sets for a feature."""
        pass

    @abstractmethod
    def get_all_by_language(self, language: SupportedLanguage) -> list[TranslationDTO]:
        """Get all translations for a language (across all features)."""
        pass

    @abstractmethod
    def create_translation_set(self, translation_set: TranslationSetDTO) -> None:
        """Create new translation set (all languages)."""
        pass

    @abstractmethod
    def update_translation(
            self,
            label: str,
            feature: str,
            language: SupportedLanguage,
            text: str
    ) -> None:
        """Update single translation text."""
        pass

    @abstractmethod
    def delete_translation_set(self, label: str, feature: str) -> None:
        """Delete entire translation set (all languages)."""
        pass

    @abstractmethod
    def get_missing_translations(self, feature: str) -> list[TranslationSetDTO]:
        """Get translation sets with at least one missing language."""
        pass

    @abstractmethod
    def load_feature_tsv(self, feature_name: str, tsv_path: str) -> int:
        """
        Load translations from TSV file for a feature.

        Returns:
            Number of translation sets loaded
        """
        pass