from abc import ABC, abstractmethod
from typing import Optional
from translation.dto.translation_dto import (
    TranslationDTO,
    TranslationSetDTO,
    CreateTranslationDTO,
    UpdateTranslationDTO
)
from translation.enum.language_enum import SupportedLanguage


class TranslationServiceInterface(ABC):
    """
    Core translation service interface.

    Responsibilities:
    - Retrieve translations (with fallback logic)
    - Manage translation CRUD (with policy checks)
    - Feature discovery and auto-loading
    - Export/Import
    - Coverage analytics
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
            feature: Feature name (e.g., "authenticator")
            fallback_to_label: Return label if translation missing?

        Returns:
            Translated text or label (if fallback enabled)

        Logs:
            Missing translations via AuditTrail
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

        Policy:
            Requires ADMIN or QMB role

        Audit:
            Logs CREATE_TRANSLATION with all languages
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

        Policy:
            Requires ADMIN or QMB role

        Audit:
            Logs UPDATE_TRANSLATION with old/new values
        """
        pass

    @abstractmethod
    def delete_translation(self, label: str, feature: str, actor_id: int) -> None:
        """
        Delete translation set (all languages).

        Policy:
            Requires ADMIN role only

        Audit:
            Logs DELETE_TRANSLATION (CRITICAL severity)
        """
        pass

    @abstractmethod
    def get_missing_for_feature(self, feature: str) -> list[TranslationSetDTO]:
        """Get all translation sets with missing languages."""
        pass

    @abstractmethod
    def get_coverage(self, feature: str) -> dict[SupportedLanguage, float]:
        """
        Calculate translation coverage per language.

        Returns:
            {DE: 0.95, EN:  1.0}  # 95% DE, 100% EN
        """
        pass

    @abstractmethod
    def load_all_features(self) -> dict[str, int]:
        """
        Auto-discover and load all <feature>/labels.tsv files.

        Returns:
            {"authenticator": 15, "user_management": 23}  # feature -> count
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
        Export feature translations.

        Formats:
            - tsv: Tab-separated (default)
            - json:  Structured JSON
            - csv: Comma-separated (Excel-compatible)
        """
        pass