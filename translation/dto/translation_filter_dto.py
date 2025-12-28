"""
Translation Filter DTO
======================

DTO for filtering translation queries.
"""

from dataclasses import dataclass
from typing import Optional

from translation.enum.translation_enum import SupportedLanguage, TranslationStatus


@dataclass(frozen=True)
class TranslationFilterDTO:
    """
    DTO for filtering translation queries.

    Attributes:
        feature: Filter by feature name (None = all features)
        language: Filter by language (None = all languages)
        status: Filter by status (None = all statuses)
        search_text: Search in labels/text (case-insensitive)
        only_missing: Show only missing translations

    Example:
    --------
        >>> filter_dto = TranslationFilterDTO(
        ...     feature="core",
        ...     language=SupportedLanguage.DE,
        ...     only_missing=True
        ... )
    """
    feature: Optional[str] = None
    language: Optional[SupportedLanguage] = None
    status: Optional[TranslationStatus] = None
    search_text: Optional[str] = None
    only_missing: bool = False

    def __post_init__(self):
        """
        Validate filter criteria.

        Raises:
            ValueError: If validation fails
        """
        if self.feature is not None:
            if not isinstance(self.feature, str):
                raise ValueError(f"Feature must be a string, got {type(self.feature).__name__}")

        if self.language is not None:
            if not isinstance(self.language, SupportedLanguage):
                raise ValueError(
                    f"Language must be SupportedLanguage enum, got {type(self.language).__name__}"
                )

        if self.status is not None:
            if not isinstance(self.status, TranslationStatus):
                raise ValueError(
                    f"Status must be TranslationStatus enum, got {type(self.status).__name__}"
                )

        if self.search_text is not None:
            if not isinstance(self.search_text, str):
                raise ValueError(
                    f"Search text must be a string, got {type(self.search_text).__name__}"
                )

        if not isinstance(self.only_missing, bool):
            raise ValueError(
                f"only_missing must be a bool, got {type(self.only_missing).__name__}"
            )