import csv
from pathlib import Path
from typing import Optional
from translation.repository.translation_repository_interface import TranslationRepositoryInterface
from translation.dto.translation_dto import TranslationDTO, TranslationSetDTO
from translation.enum.language_enum import SupportedLanguage
from translation.enum.translation_status_enum import TranslationStatus
from translation.exceptions.translation_exceptions import TranslationLoadError


class TSVTranslationRepository(TranslationRepositoryInterface):
    """
    TSV-based implementation of TranslationRepository.

    Storage format (per feature):
        <feature_dir>/labels.tsv:
        label\tde\ten
        core.save\tSpeichern\tSave
        core.cancel\tAbbrechen\tCancel

    In-memory structure:
        {
            "authenticator": {
                "auth. login": TranslationSetDTO(... ),
                "auth.logout":  TranslationSetDTO(...)
            },
            "user_management": {... }
        }
    """

    def __init__(self):
        self._storage: dict[str, dict[str, TranslationSetDTO]] = {}
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
        """Get all language variants."""
        return self._storage.get(feature, {}).get(label)

    def get_all_by_feature(self, feature: str) -> list[TranslationSetDTO]:
        """Get all translations for a feature."""
        return list(self._storage.get(feature, {}).values())

    def get_all_by_language(self, language: SupportedLanguage) -> list[TranslationDTO]:
        """Get all translations for a language."""
        results = []
        for feature, translations in self._storage.items():
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
                    feature=feature,
                    status=status
                ))
        return results

    def create_translation_set(self, translation_set: TranslationSetDTO) -> None:
        """Create new translation set."""
        if translation_set.feature not in self._storage:
            self._storage[translation_set.feature] = {}

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
            raise ValueError(f"Translation set not found:  {feature}. {label}")

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
        if feature in self._storage and label in self._storage[feature]:
            del self._storage[feature][label]

    def get_missing_translations(self, feature: str) -> list[TranslationSetDTO]:
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
            TranslationLoadError: If TSV format invalid
        """
        path = Path(tsv_path)
        if not path.exists():
            raise TranslationLoadError(f"TSV file not found: {tsv_path}")

        try:
            with path.open(encoding="utf-8") as f:
                reader = csv.reader(f, delimiter="\t")
                header = next(reader)

                # Validate header
                if header[0] != "label":
                    raise TranslationLoadError(
                        f"Invalid TSV header.  Expected 'label', got '{header[0]}'"
                    )

                # Parse language columns
                lang_columns = []
                for col in header[1:]:
                    try:
                        lang_columns.append(SupportedLanguage.from_string(col))
                    except ValueError as e:
                        raise TranslationLoadError(f"Invalid language in header: {col}") from e

                # Load rows
                if feature_name not in self._storage:
                    self._storage[feature_name] = {}

                count = 0
                for row in reader:
                    if not row or not row[0].strip():
                        continue  # Skip empty rows

                    label = row[0]
                    translations = {}

                    for i, lang in enumerate(lang_columns):
                        text = row[i + 1] if i + 1 < len(row) else ""
                        translations[lang] = text

                    translation_set = TranslationSetDTO(
                        label=label,
                        feature=feature_name,
                        translations=translations
                    )
                    self._storage[feature_name][label] = translation_set
                    count += 1

                return count

        except Exception as e:
            raise TranslationLoadError(
                f"Failed to load TSV for feature '{feature_name}': {str(e)}"
            ) from e

    def persist_feature_tsv(self, feature_name: str, tsv_path: str) -> None:
        """
        Write feature translations back to TSV file.

        ATOMIC write (tmp file + rename) to prevent corruption.
        """
        feature_translations = self._storage.get(feature_name, {})
        if not feature_translations:
            return

        path = Path(tsv_path)
        tmp_path = path.with_suffix(".tmp")

        try:
            with tmp_path.open("w", encoding="utf-8", newline="") as f:
                writer = csv.writer(f, delimiter="\t")

                # Write header
                writer.writerow(["label"] + SupportedLanguage.all_codes())

                # Write rows (sorted by label)
                for label in sorted(feature_translations.keys()):
                    trans_set = feature_translations[label]
                    row = [label]
                    for lang in SupportedLanguage:
                        row.append(trans_set.translations.get(lang, ""))
                    writer.writerow(row)

            # Atomic replace
            tmp_path.replace(path)

        except Exception as e:
            if tmp_path.exists():
                tmp_path.unlink()
            raise TranslationLoadError(
                f"Failed to persist TSV for feature '{feature_name}': {str(e)}"
            ) from e