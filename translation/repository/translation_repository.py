"""
Translation Repository Implementations
=======================================

Concrete implementations of TranslationRepositoryInterface. 

Implementations:
----------------
- InMemoryTranslationRepository: Primary implementation (dict-based)
- TSVTranslationRepository: TSV file-based (extends in-memory with persistence)
"""

import csv
from pathlib import Path
from typing import Dict, List, Optional

from translation.repository.translation_repository_interface import TranslationRepositoryInterface
from translation.dto.translation_dto import TranslationDTO, TranslationSetDTO
from translation.enum.translation_enum import SupportedLanguage, TranslationStatus
from translation.exceptions.translation_exceptions import (
    TranslationNotFoundError,
    TranslationAlreadyExistsError,
    TranslationLoadError,
    InvalidLanguageError,
)


class InMemoryTranslationRepository(TranslationRepositoryInterface):
    """
    In-memory translation repository using nested dictionaries.

    Storage structure:
    ------------------
        {
            "core":  {
                "core.save": TranslationSetDTO(... ),
                "core.cancel":  TranslationSetDTO(...)
            },
            "authenticator": {
                "auth.login": TranslationSetDTO(...)
            }
        }

    Thread Safety:
    --------------
    NOT thread-safe by default.  For multi-threaded access, wrap methods
    with locks or use a thread-safe dict implementation.

    Usage:
    ------
        >>> repo = InMemoryTranslationRepository()
        >>> repo.load_feature_tsv("core", "core/labels.tsv")
        25
        >>> dto = repo.get_translation("core.save", SupportedLanguage.DE, "core")
        >>> dto.text
        'Speichern'
    """

    def __init__(self):
        """Initialize empty repository."""
        self._storage: Dict[str, Dict[str, TranslationSetDTO]] = {}
        # feature_name -> {label -> TranslationSetDTO}

    def get_translation(
            self,
            label: str,
            language: SupportedLanguage,
            feature: str
    ) -> Optional[TranslationDTO]:
        """Retrieve single translation."""
        translation_set = self._storage.get(feature, {}).get(label)
        if not translation_set:
            return None

        text = translation_set.translations.get(language, "")
        status = (
            TranslationStatus.MISSING if not text.strip()
            else TranslationStatus.COMPLETE
        )

        return TranslationDTO(
            label=label,
            language=language,
            text=text,
            feature=feature,
            status=status
        )

    def get_translation_set(self, label: str, feature: str) -> Optional[TranslationSetDTO]:
        """Get complete translation set."""
        return self._storage.get(feature, {}).get(label)

    def get_all_by_feature(self, feature: str) -> List[TranslationSetDTO]:
        """Get all translation sets for a feature."""
        return list(self._storage.get(feature, {}).values())

    def get_all_by_language(self, language: SupportedLanguage) -> List[TranslationDTO]:
        """Get all translations for a language."""
        results = []
        for feature_name, translations in self._storage.items():
            for label, trans_set in translations.items():
                text = trans_set.translations.get(language, "")
                status = (
                    TranslationStatus.MISSING if not text.strip()
                    else TranslationStatus.COMPLETE
                )
                results.append(TranslationDTO(
                    label=label,
                    language=language,
                    text=text,
                    feature=feature_name,
                    status=status
                ))
        return results

    def get_all_features(self) -> List[str]:
        """Get list of all loaded features."""
        return list(self._storage.keys())

    def create_translation_set(self, translation_set: TranslationSetDTO) -> None:
        """Create new translation set."""
        if translation_set.feature not in self._storage:
            self._storage[translation_set.feature] = {}

        if translation_set.label in self._storage[translation_set.feature]:
            raise TranslationAlreadyExistsError(
                f"Translation already exists:  {translation_set.feature}. {translation_set.label}"
            )

        self._storage[translation_set.feature][translation_set.label] = translation_set

    def update_translation(
            self,
            label: str,
            feature: str,
            language: SupportedLanguage,
            text: str
    ) -> None:
        """Update single translation."""
        translation_set = self._storage.get(feature, {}).get(label)
        if not translation_set:
            raise TranslationNotFoundError(
                f"Translation set not found: {feature}.{label}"
            )

        # Create updated set (immutable DTO)
        updated_translations = {**translation_set.translations, language: text}
        updated_set = TranslationSetDTO(
            label=label,
            feature=feature,
            translations=updated_translations
        )
        self._storage[feature][label] = updated_set

    def delete_translation_set(self, label: str, feature: str) -> None:
        """Delete translation set."""
        if feature not in self._storage or label not in self._storage[feature]:
            raise TranslationNotFoundError(
                f"Translation set not found: {feature}.{label}"
            )

        del self._storage[feature][label]

    def get_missing_translations(self, feature: str) -> List[TranslationSetDTO]:
        """Get translation sets with missing languages."""
        feature_translations = self._storage.get(feature, {})
        return [
            trans_set for trans_set in feature_translations.values()
            if trans_set.get_missing_languages()
        ]

    def load_feature_tsv(self, feature_name: str, tsv_path: str) -> int:
        """
        Load TSV file for a feature. 

        Expected format:
            label\tde\ten
            auth.login\tAnmelden\tLogin

        Returns:
            Number of translation sets loaded

        Raises: 
            TranslationLoadError: If TSV format invalid or file not found
        """
        path = Path(tsv_path)
        if not path.exists():
            raise TranslationLoadError(f"TSV file not found: {tsv_path}")

        try:
            with path.open(encoding="utf-8") as f:
                reader = csv.reader(f, delimiter="\t")
                header = next(reader)

                # Validate header
                if not header or header[0] != "label":
                    raise TranslationLoadError(
                        f"Invalid TSV header.  Expected 'label' as first column, got '{header[0] if header else 'empty'}'"
                    )

                # Parse language columns
                lang_columns = []
                for col in header[1:]:
                    try:
                        lang_columns.append(SupportedLanguage.from_string(col))
                    except ValueError as e:
                        raise InvalidLanguageError(
                            f"Unsupported language in TSV header: {col}"
                        ) from e

                # Initialize feature storage
                if feature_name not in self._storage:
                    self._storage[feature_name] = {}

                # Load rows
                count = 0
                for row_num, row in enumerate(reader, start=2):  # Start at 2 (header is 1)
                    if not row or not row[0].strip():
                        continue  # Skip empty rows

                    label = row[0]
                    translations = {}

                    for i, lang in enumerate(lang_columns):
                        text = row[i + 1] if i + 1 < len(row) else ""
                        translations[lang] = text

                    try:
                        translation_set = TranslationSetDTO(
                            label=label,
                            feature=feature_name,
                            translations=translations
                        )
                        self._storage[feature_name][label] = translation_set
                        count += 1
                    except ValueError as e:
                        raise TranslationLoadError(
                            f"Invalid translation data at row {row_num}: {str(e)}"
                        ) from e

                return count

        except TranslationLoadError:
            raise
        except InvalidLanguageError:
            raise
        except Exception as e:
            raise TranslationLoadError(
                f"Failed to load TSV for feature '{feature_name}': {str(e)}"
            ) from e

    def persist_feature_tsv(self, feature_name: str, tsv_path: str) -> None:
        """
        Write feature translations to TSV file (atomic write).

        Uses temp file + rename for atomic operation (prevents corruption).
        """
        feature_translations = self._storage.get(feature_name, {})
        if not feature_translations:
            # Nothing to persist, but not an error
            return

        path = Path(tsv_path)
        tmp_path = path.with_suffix(". tmp")

        try:
            # Ensure directory exists
            path.parent.mkdir(parents=True, exist_ok=True)

            with tmp_path.open("w", encoding="utf-8", newline="") as f:
                writer = csv.writer(f, delimiter="\t")

                # Write header
                writer.writerow(["label"] + SupportedLanguage.all_codes())

                # Write rows (sorted by label for consistency)
                for label in sorted(feature_translations.keys()):
                    trans_set = feature_translations[label]
                    row = [label]
                    for lang in SupportedLanguage:
                        row.append(trans_set.translations.get(lang, ""))
                    writer.writerow(row)

            # Atomic replace
            tmp_path.replace(path)

        except Exception as e:
            # Cleanup temp file on error
            if tmp_path.exists():
                tmp_path.unlink()
            raise TranslationLoadError(
                f"Failed to persist TSV for feature '{feature_name}': {str(e)}"
            ) from e

    def get_coverage(self, feature: str) -> Dict[SupportedLanguage, float]:
        """
        Calculate translation coverage per language. 

        Coverage = (complete translations) / (total translations)
        """
        all_translations = self._storage.get(feature, {})
        if not all_translations:
            return {lang: 0.0 for lang in SupportedLanguage}

        total = len(all_translations)
        coverage = {}

        for lang in SupportedLanguage:
            complete_count = sum(
                1 for trans_set in all_translations.values()
                if lang in trans_set.translations and trans_set.translations[lang].strip()
            )
            coverage[lang] = complete_count / total if total > 0 else 0.0

        return coverage


class TSVTranslationRepository(InMemoryTranslationRepository):
    """
    TSV-based translation repository (extends InMemoryTranslationRepository).

    Differences from InMemory:
    --------------------------
    - Auto-persists changes to TSV files
    - Can be initialized with auto-load from directory

    Usage:
    ------
        >>> repo = TSVTranslationRepository()
        >>> repo.load_feature_tsv("core", "core/labels.tsv")
        >>> repo.update_translation("core.save", "core", SupportedLanguage. DE, "Neu")
        >>> repo.persist_feature_tsv("core", "core/labels.tsv")  # Save changes

    Future Enhancement:
    -------------------
    - Auto-persist on every update (with configurable delay)
    - Watch TSV files for external changes
    - Merge conflicts resolution
    """

    def __init__(self, auto_persist: bool = False):
        """
        Initialize TSV repository.

        Args:
            auto_persist: If True, automatically persist changes to TSV files
        """
        super().__init__()
        self._auto_persist = auto_persist
        self._tsv_paths: Dict[str, str] = {}  # feature -> tsv_path mapping

    def load_feature_tsv(self, feature_name: str, tsv_path: str) -> int:
        """Load TSV and remember path for auto-persist."""
        count = super().load_feature_tsv(feature_name, tsv_path)
        self._tsv_paths[feature_name] = tsv_path
        return count

    def update_translation(
            self,
            label: str,
            feature: str,
            language: SupportedLanguage,
            text: str
    ) -> None:
        """Update translation and auto-persist if enabled."""
        super().update_translation(label, feature, language, text)

        if self._auto_persist and feature in self._tsv_paths:
            self.persist_feature_tsv(feature, self._tsv_paths[feature])

    def create_translation_set(self, translation_set: TranslationSetDTO) -> None:
        """Create translation set and auto-persist if enabled."""
        super().create_translation_set(translation_set)

        if self._auto_persist and translation_set.feature in self._tsv_paths:
            self.persist_feature_tsv(
                translation_set.feature,
                self._tsv_paths[translation_set.feature]
            )

    def delete_translation_set(self, label: str, feature: str) -> None:
        """Delete translation set and auto-persist if enabled."""
        super().delete_translation_set(label, feature)

        if self._auto_persist and feature in self._tsv_paths:
            self.persist_feature_tsv(feature, self._tsv_paths[feature])