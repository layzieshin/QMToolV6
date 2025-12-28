"""
Translation Service Interface
==============================

Abstract interface for translation business logic.

Responsibilities:
-----------------
- Retrieve translations (with fallback logic)
- Manage translation CRUD (with policy checks)
- Feature discovery and auto-loading
- Export/Import
- Coverage analytics
- Audit trail integration
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict

from translation.dto.translation_dto import (
    TranslationDTO,
    TranslationSetDTO,
    CreateTranslationDTO,
    UpdateTranslationDTO,
)
from translation.dto.translation_filter_dto import TranslationFilterDTO
from translation.enum.translation_enum import SupportedLanguage


class TranslationServiceInterface(ABC):
    """
    Abstract interface for translation service.

    All methods that modify data require actor_id for:
    - Policy enforcement (authorization)
    - Audit trail logging

    Usage Pattern:
    --------------
        service = TranslationService(...)

        # Read operations (no actor needed)
        text = service.get("core. save", SupportedLanguage.DE, "core")

        # Write operations (require actor)
        service.create_translation(dto, actor_id=admin_id)
    """

    @abstractmethod
    def get(
            self,
            label: str,
            language: SupportedLanguage,
            feature: str,
            fallback_to_label: bool = True
    ) -> str:
        """
        Get translation text (primary public API).

        Args:
            label: Translation key (e.g., "core.save")
            language: Target language
            feature: Feature name (e.g., "core")
            fallback_to_label: Return label if translation missing?

        Returns:
            Translated text or label (if fallback enabled)

        Behavior:
        ---------
        - If translation exists: return text
        - If missing and fallback=True: return label
        - If missing and fallback=False: return empty string
        - Logs missing translations via AuditTrail (once per key)

        Example:
        --------
            >>> service. get("core.save", SupportedLanguage.DE, "core")
            'Speichern'

            >>> service.get("missing.key", SupportedLanguage.EN, "core")
            'missing.key'  # Fallback to label
        """
        pass

    @abstractmethod
    def get_translation(
            self,
            label: str,
            language: SupportedLanguage,
            feature: str
    ) -> Optional[TranslationDTO]:
        """
        Get full TranslationDTO (with metadata).

        Args:
            label: Translation key
            language: Target language
            feature: Feature name

        Returns:
            TranslationDTO if found, None otherwise

        Example:
        --------
            >>> dto = service.get_translation("core.save", SupportedLanguage.DE, "core")
            >>> dto.status
            <TranslationStatus.COMPLETE: 'complete'>
        """
        pass

    @abstractmethod
    def get_translation_set(self, label: str, feature: str) -> Optional[TranslationSetDTO]:
        """
        Get complete translation set (all languages).

        Args:
            label: Translation key
            feature: Feature name

        Returns:
            TranslationSetDTO if found, None otherwise

        Example:
        --------
            >>> set_dto = service. get_translation_set("core. save", "core")
            >>> set_dto.translations[SupportedLanguage.DE]
            'Speichern'
        """
        pass

    @abstractmethod
    def query_translations(self, filter_dto: TranslationFilterDTO) -> List[TranslationSetDTO]:
        """
        Query translations with filter criteria.

        Args:
            filter_dto: Filter criteria

        Returns:
            List of matching TranslationSetDTO

        Example:
        --------
            >>> filter_dto = TranslationFilterDTO(feature="core", only_missing=True)
            >>> results = service.query_translations(filter_dto)
        """
        pass

    @abstractmethod
    def create_translation(
            self,
            dto: CreateTranslationDTO,
            actor_id: int
    ) -> TranslationSetDTO:
        """
        Create new translation set.

        Args:
            dto: Translation data
            actor_id: User performing the action

        Returns:
            Created TranslationSetDTO

        Raises:
            TranslationPermissionError: If actor lacks permission
            TranslationAlreadyExistsError: If translation exists

        Policy:
            Requires ADMIN or QMB role

        Audit:
            Logs CREATE with all languages

        Example:
        --------
            >>> dto = CreateTranslationDTO(
            ...     label="new.key",
            ...     feature="core",
            ...     translations={SupportedLanguage.DE:  "Neu", SupportedLanguage.EN:  "New"}
            ... )
            >>> service.create_translation(dto, actor_id=admin_id)
        """
        pass

    @abstractmethod
    def update_translation(
            self,
            dto: UpdateTranslationDTO,
            actor_id: int
    ) -> TranslationDTO:
        """
        Update single translation.

        Args:
            dto: Update data
            actor_id: User performing the action

        Returns:
            Updated TranslationDTO

        Raises:
            TranslationPermissionError:  If actor lacks permission
            TranslationNotFoundError: If translation not found

        Policy:
            Requires ADMIN or QMB role

        Audit:
            Logs UPDATE with old/new values

        Example:
        --------
            >>> dto = UpdateTranslationDTO(
            ...      label="core.save",
            ...     feature="core",
            ...     language=SupportedLanguage.DE,
            ...     text="Speichern (aktualisiert)"
            ... )
            >>> service.update_translation(dto, actor_id=admin_id)
        """
        pass

    @abstractmethod
    def delete_translation(self, label: str, feature: str, actor_id: int) -> None:
        """
        Delete translation set (all languages).

        Args:
            label: Translation key
            feature: Feature name
            actor_id: User performing the action

        Raises:
            TranslationPermissionError: If actor lacks permission (requires ADMIN)
            TranslationNotFoundError: If translation not found

        Policy:
            Requires ADMIN role only

        Audit:
            Logs DELETE (CRITICAL severity)

        Example:
        --------
            >>> service. delete_translation("old.key", "core", actor_id=admin_id)
        """
        pass

    @abstractmethod
    def get_missing_for_feature(self, feature: str) -> List[TranslationSetDTO]:
        """
        Get all translation sets with missing languages for a feature.

        Args:
            feature: Feature name

        Returns:
            List of TranslationSetDTO with incomplete translations

        Example:
        --------
            >>> missing = service.get_missing_for_feature("core")
            >>> for set_dto in missing:
            ...     print(set_dto.label, set_dto.get_missing_languages())
        """
        pass

    @abstractmethod
    def get_coverage(self, feature: str) -> Dict[SupportedLanguage, float]:
        """
        Calculate translation coverage per language for a feature.

        Args:
            feature: Feature name

        Returns:
            Dict mapping language to coverage (0.0 - 1.0)

        Example:
        --------
            >>> coverage = service.get_coverage("core")
            >>> coverage[SupportedLanguage.DE]
            0.96  # 96% coverage
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
            >>> service.get_all_features()
            ['core', 'authenticator', 'user_management', 'translation']
        """
        pass

    @abstractmethod
    def load_all_features(self) -> Dict[str, int]:
        """
        Auto-discover and load all <feature>/labels.tsv files.

        Returns:
            Dict mapping feature_name to count of loaded translation sets

        Behavior:
        ---------
        - Scans project root for directories with meta. json
        - Loads labels. tsv if exists
        - Logs errors via AuditTrail but continues

        Example:
        --------
            >>> loaded = service.load_all_features()
            >>> loaded
            {'authenticator': 15, 'user_management': 23, 'core': 25}
        """
        pass

    @abstractmethod
    def export_feature(
            self,
            feature: str,
            output_path: str,
            format: str = "tsv"
    ) -> None:
        """
        Export feature translations to file.

        Args:
            feature: Feature name
            output_path: Output file path
            format: Export format ("tsv", "json", "csv")

        Raises:
            ValueError: If format not supported
            TranslationLoadError: If export fails

        Formats:
        --------
        - tsv: Tab-separated (default, preserves original format)
        - json:  Structured JSON (for APIs)
        - csv: Comma-separated (Excel-compatible)

        Example:
        --------
            >>> service. export_feature("core", "exports/core.tsv", format="tsv")
            >>> service.export_feature("core", "exports/core.json", format="json")
        """
        pass