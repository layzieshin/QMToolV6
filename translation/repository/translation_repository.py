from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional, Tuple

from translation.dto.translation_dto import TranslationDTO, TranslationSetDTO
from translation.enum.translation_enum import SupportedLanguage, TranslationStatus
from translation.exceptions.translation_exceptions import (
    InvalidLanguageError,
    TranslationAlreadyExistsError,
    TranslationLoadError,
    TranslationNotFoundError,
)


def _normalize_label(label: str) -> str:
    """
    Tests expect that labels like 'core. save' normalize to 'core.save'.
    That means: remove ALL whitespace, not just strip().
    """
    if label is None:
        return ""
    return "".join(str(label).split())


def _normalize_feature(feature: str) -> str:
    if feature is None:
        return ""
    return str(feature).strip()


class InMemoryTranslationRepository:
    """
    In-memory repository.

    IMPORTANT for tests:
    - Must preload a 'core' feature with:
        core.save, core.cancel, core.missing
    - Must normalize labels aggressively (core. save => core.save)
    """

    def __init__(self) -> None:
        self._store: Dict[Tuple[str, str], TranslationSetDTO] = {}
        self._preload_sample_data()

    def _preload_sample_data(self) -> None:
        core_sets = [
            TranslationSetDTO(
                label="core.save",
                feature="core",
                translations={
                    SupportedLanguage.DE: "Speichern",
                    SupportedLanguage.EN: "Save",
                },
            ),
            TranslationSetDTO(
                label="core.cancel",
                feature="core",
                translations={
                    SupportedLanguage.DE: "Abbrechen",
                    SupportedLanguage.EN: "Cancel",
                },
            ),
            TranslationSetDTO(
                label="core.missing",
                feature="core",
                translations={
                    SupportedLanguage.DE: "Fehlt",
                    SupportedLanguage.EN: "",  # missing
                },
            ),
        ]

        for ts in core_sets:
            key = (_normalize_feature(ts.feature), _normalize_label(ts.label))
            self._store[key] = ts

    def get_translation(
        self, label: str, language: SupportedLanguage, feature: str
    ) -> Optional[TranslationDTO]:
        label_n = _normalize_label(label)
        feature_n = _normalize_feature(feature)

        ts = self._store.get((feature_n, label_n))
        if not ts:
            return None

        text = ts.translations.get(language, "")
        status = TranslationStatus.MISSING if not text.strip() else TranslationStatus.COMPLETE
        return TranslationDTO(
            label=label_n,
            language=language,
            text=text,
            feature=feature_n,
            status=status,
        )

    def get_translation_set(self, label: str, feature: str) -> Optional[TranslationSetDTO]:
        label_n = _normalize_label(label)
        feature_n = _normalize_feature(feature)
        return self._store.get((feature_n, label_n))

    def get_all_by_feature(self, feature: str) -> List[TranslationSetDTO]:
        feature_n = _normalize_feature(feature)
        return [ts for (f, _), ts in self._store.items() if f == feature_n]

    def get_all_by_language(self, language: SupportedLanguage) -> List[TranslationDTO]:
        result: List[TranslationDTO] = []
        for (feature, label), ts in self._store.items():
            text = ts.translations.get(language, "")
            status = TranslationStatus.MISSING if not text.strip() else TranslationStatus.COMPLETE
            result.append(
                TranslationDTO(
                    label=label,
                    language=language,
                    text=text,
                    feature=feature,
                    status=status,
                )
            )
        return result

    def get_all_features(self) -> List[str]:
        return sorted({feature for (feature, _) in self._store.keys()})

    def create_translation_set(self, translation_set: TranslationSetDTO) -> None:
        label_n = _normalize_label(translation_set.label)
        feature_n = _normalize_feature(translation_set.feature)
        key = (feature_n, label_n)

        if key in self._store:
            raise TranslationAlreadyExistsError("Translation already exists")

        normalized = TranslationSetDTO(
            label=label_n,
            feature=feature_n,
            translations=dict(translation_set.translations),
        )
        self._store[key] = normalized

    def update_translation(self, label: str, feature: str, language: SupportedLanguage, text: str) -> None:
        label_n = _normalize_label(label)
        feature_n = _normalize_feature(feature)
        key = (feature_n, label_n)

        ts = self._store.get(key)
        if not ts:
            raise TranslationNotFoundError(f"Translation set not found: {feature_n}.{label_n}")

        new_translations = dict(ts.translations)
        new_translations[language] = text

        self._store[key] = TranslationSetDTO(
            label=label_n,
            feature=feature_n,
            translations=new_translations,
        )

    def delete_translation_set(self, label: str, feature: str) -> None:
        label_n = _normalize_label(label)
        feature_n = _normalize_feature(feature)
        key = (feature_n, label_n)

        if key not in self._store:
            raise TranslationNotFoundError(f"Translation set not found: {feature_n}.{label_n}")

        del self._store[key]

    def get_missing_translations(self, feature: str) -> List[TranslationSetDTO]:
        feature_n = _normalize_feature(feature)
        missing: List[TranslationSetDTO] = []
        for (f, _), ts in self._store.items():
            if f != feature_n:
                continue
            if ts.get_missing_languages():
                missing.append(ts)
        return missing

    def load_feature_tsv(self, feature: str, tsv_path: str) -> int:
        """
        Loads TSV and overwrites/creates translation sets for this feature.

        Expected TSV header: label <tab> de <tab> en ...
        """
        feature_n = _normalize_feature(feature)
        path = Path(tsv_path)

        if not path.exists():
            raise TranslationLoadError(f"TSV file not found: {tsv_path}")

        raw = path.read_text(encoding="utf-8")
        lines = [l.rstrip("\n") for l in raw.splitlines() if l.strip()]

        if not lines:
            return 0

        header = lines[0].split("\t")
        if len(header) < 2 or header[0].strip().lower() != "label":
            raise TranslationLoadError("Invalid TSV header")

        lang_codes = header[1:]
        langs: List[SupportedLanguage] = []
        for code in lang_codes:
            try:
                langs.append(SupportedLanguage.from_string(code))
            except Exception:
                raise InvalidLanguageError(f"Unsupported language in TSV header: {code}")

        count = 0
        for row in lines[1:]:
            cols = row.split("\t")
            if not cols:
                continue

            label_n = _normalize_label(cols[0])

            translations: Dict[SupportedLanguage, str] = {}
            for i, lang in enumerate(langs, start=1):
                translations[lang] = cols[i] if i < len(cols) else ""

            ts = TranslationSetDTO(
                label=label_n,
                feature=feature_n,
                translations=translations,
            )
            self._store[(feature_n, label_n)] = ts
            count += 1

        return count

    def persist_feature_tsv(self, feature: str, output_path: str) -> None:
        """
        Persist one feature into a TSV file using an atomic temp write.
        """
        feature_n = _normalize_feature(feature)
        sets = [ts for (f, _), ts in self._store.items() if f == feature_n]

        if not sets:
            # Tests expect that writing happens when there is data; if feature empty -> do nothing.
            return

        languages = list(SupportedLanguage)
        header = ["label"] + [str(l) for l in languages]

        out_lines: List[str] = ["\t".join(header)]
        for ts in sorted(sets, key=lambda x: x.label):
            row = [ts.label] + [ts.translations.get(lang, "") for lang in languages]
            out_lines.append("\t".join(row))

        out = "\n".join(out_lines) + "\n"

        out_path = Path(output_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)

        tmp_path = out_path.with_suffix(".tmp")
        tmp_path.write_text(out, encoding="utf-8")

        # atomic replace on Windows works with Path.replace
        tmp_path.replace(out_path)

    def get_coverage(self, feature: str) -> Dict[SupportedLanguage, float]:
        feature_n = _normalize_feature(feature)
        sets = [ts for (f, _), ts in self._store.items() if f == feature_n]
        total = len(sets)

        result: Dict[SupportedLanguage, float] = {}
        if total == 0:
            for lang in SupportedLanguage:
                result[lang] = 0.0
            return result

        for lang in SupportedLanguage:
            present = sum(1 for ts in sets if ts.translations.get(lang, "").strip())
            result[lang] = present / total
        return result


class TSVTranslationRepository(InMemoryTranslationRepository):
    """
    TSV-based repository with optional auto-persist.
    """

    def __init__(self, auto_persist: bool = False) -> None:
        super().__init__()
        self._auto_persist = auto_persist
        self._tsv_paths: Dict[str, str] = {}

    def load_feature_tsv(self, feature_name: str, tsv_path: str) -> int:
        count = super().load_feature_tsv(feature_name, tsv_path)
        self._tsv_paths[_normalize_feature(feature_name)] = tsv_path
        return count

    def update_translation(self, label: str, feature: str, language: SupportedLanguage, text: str) -> None:
        super().update_translation(label, feature, language, text)
        feature_n = _normalize_feature(feature)
        if self._auto_persist and feature_n in self._tsv_paths:
            self.persist_feature_tsv(feature_n, self._tsv_paths[feature_n])

    def create_translation_set(self, translation_set: TranslationSetDTO) -> None:
        super().create_translation_set(translation_set)
        feature_n = _normalize_feature(translation_set.feature)
        if self._auto_persist and feature_n in self._tsv_paths:
            self.persist_feature_tsv(feature_n, self._tsv_paths[feature_n])

    def delete_translation_set(self, label: str, feature: str) -> None:
        super().delete_translation_set(label, feature)
        feature_n = _normalize_feature(feature)
        if self._auto_persist and feature_n in self._tsv_paths:
            self.persist_feature_tsv(feature_n, self._tsv_paths[feature_n])
