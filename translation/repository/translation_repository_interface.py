"""
Translation Repository Interface
=================================

Abstract interface for translation storage.

Implementations can be:
- In-memory (for testing/development)
- TSV-based (current V4 approach)
- Database-based (future SQL storage)
- Hybrid (TSV for dev, DB for production)
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict

from translation.dto.translation_dto import TranslationDTO, TranslationSetDTO
from translation.enum.translation_enum import SupportedLanguage


class TranslationRepositoryInterface(ABC):
    """
    Abstract repository for translation data access.

    Responsibilities:
    -----------------
    - CRUD operations for translation sets
    - Query by feature/language/label
    - Load/persist TSV files
    - Detect missing translations

    Implementation Notes:
    ---------------------
    - All methods should be thread-safe (if needed)
    - DTOs are immutable, return new instances
    - Errors should raise specific TranslationException subclasses
    """

    @abstractmethod
    def get_translation(
            self,
            label: str,
            language: SupportedLanguage,
            feature: str
    ) -> Optional[TranslationDTO]:
        """
        Retrieve a single translation.

        Args:
            label: Translation key (e.g., "core. save")
            language: Target language
            feature: Feature name (e.g., "core")

        Returns:
            TranslationDTO if found, None otherwise

        Example:
        --------
            >>> dto = repo.get_translation("core.save", SupportedLanguage.DE, "core")
            >>> dto.text
            'Speichern'
        """
        pass

    @abstractmethod
    def get_translation_set(self, label: str, feature: str) -> Optional[TranslationSetDTO]:
        """
        Get complete translation set (all languages) for a label.

        Args:
            label: Translation key
            feature: Feature name

        Returns:
            TranslationSetDTO if found, None otherwise

        Example:
        --------
            >>> set_dto = repo. get_translation_set("core. save", "core")
            >>> set_dto.translations[SupportedLanguage.DE]
            'Speichern'
        """
        pass

    @abstractmethod
    def get_all_by_feature(self, feature: str) -> List[TranslationSetDTO]:
        """
        Get all translation sets for a feature.

        Args:
            feature: Feature name

        Returns:
            List of TranslationSetDTO (empty if feature not found)

        Example:
        --------
            >>> sets = repo.get_all_by_feature("core")
            >>> len(sets)
            25
        """
        pass

    @abstractmethod
    def get_all_by_language(self, language: SupportedLanguage) -> List[TranslationDTO]:
        """
        Get all translations for a specific language (across all features).

        Args:
            language: Target language

        Returns:
            List of TranslationDTO

        Example:
        --------
            >>> translations = repo.get_all_by_language(SupportedLanguage.DE)
            >>> len(translations)
            150
        """
        pass

    @abstractmethod
    def get_all_features(self) -> List[str]:
        """
        Get list of all features with loaded translations.

        Returns:
            List of feature names

        Example:
        --------
            >>> repo.get_all_features()
            ['core', 'authenticator', 'user_management']
        """
        pass

    @abstractmethod
    def create_translation_set(self, translation_set: TranslationSetDTO) -> None:
        """
        Create a new translation set.

        Args:
            translation_set:  Complete translation set to create

        Raises:
            TranslationAlreadyExistsError: If label/feature combination exists

        Example:
        --------
            >>> set_dto = TranslationSetDTO(
            ...     label="new. key",
            ...     feature="core",
            ...     translations={SupportedLanguage.DE: "Text"}
            ... )
            >>> repo.create_translation_set(set_dto)
        """
        pass

    @abstractmethod
    def update_translation(
            self,
            label: str,
            feature: str,
            language: SupportedLanguage,
            text: str
    ) -> None:
        """
        Update a single translation text.

        Args:
            label: Translation key
            feature: Feature name
            language: Language to update
            text: New translation text

        Raises:
            TranslationNotFoundError: If translation set not found

        Example:
        --------
            >>> repo.update_translation("core.save", "core", SupportedLanguage.DE, "Neu")
        """
        pass

    @abstractmethod
    def delete_translation_set(self, label: str, feature: str) -> None:
        """
        Delete entire translation set (all languages).

        Args:
            label: Translation key
            feature: Feature name

        Raises:
            TranslationNotFoundError: If translation set not found

        Example:
        --------
            >>> repo.delete_translation_set("old.key", "core")
        """
        pass

    @abstractmethod
    def get_missing_translations(self, feature: str) -> List[TranslationSetDTO]:
        """
        Get translation sets with at least one missing language.

        Args:
            feature: Feature name

        Returns:
            List of TranslationSetDTO with incomplete translations

        Example:
        --------
            >>> missing = repo.get_missing_translations("core")
            >>> for set_dto in missing:
            ...     print(set_dto. label, set_dto.get_missing_languages())
            core.new_key [<SupportedLanguage.EN:  'en'>]
        """
        pass

    @abstractmethod
    def load_feature_tsv(self, feature_name: str, tsv_path: str) -> int:
        """
        Load translations from TSV file into repository.

        Expected TSV format:
            label\tde\ten
            core. save\tSpeichern\tSave
            core.cancel\tAbbrechen\tCancel

        Args:
            feature_name: Name of the feature
            tsv_path: Path to TSV file

        Returns:
            Number of translation sets loaded

        Raises:
            TranslationLoadError: If file not found or invalid format

        Example:
        --------
            >>> count = repo.load_feature_tsv("core", "core/labels.tsv")
            >>> count
            25
        """
        pass

    @abstractmethod
    def persist_feature_tsv(self, feature_name: str, tsv_path: str) -> None:
        """
        Write feature translations to TSV file (atomic write).

        Args:
            feature_name: Name of the feature
            tsv_path:  Output path for TSV file

        Raises:
            TranslationLoadError: If write fails

        Example:
        --------
            >>> repo. persist_feature_tsv("core", "core/labels.tsv")
        """
        pass

    @abstractmethod
    def get_coverage(self, feature: str) -> Dict[SupportedLanguage, float]:
        """
        Calculate translation coverage per language for a feature.

        Args:
            feature: Feature name

        Returns:
            Dict mapping language to coverage percentage (0.0 - 1.0)

        Example:
        --------
            >>> coverage = repo.get_coverage("core")
            >>> coverage
            {<SupportedLanguage.DE:  'de'>: 0.96, <SupportedLanguage.EN: 'en'>: 1.0}
        """
        pass