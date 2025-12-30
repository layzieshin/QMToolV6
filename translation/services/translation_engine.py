from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, Optional, Set


@dataclass(frozen=True)
class FeatureDescriptor:
    """
    Minimal descriptor required by the translation engine.

    Only the feature id and its root path are needed to locate labels.tsv.
    """

    id: str
    root_path: Path


class TranslationEngine:
    """
    Lightweight translation engine that follows the MASTERPROMPT contract.

    Duplicate keys inside a single labels.tsv are allowed; if translations differ,
    the last occurrence wins and a single I18N_DUPLICATE_KEY log entry is emitted.
    """

    def __init__(self, *, default_language: str = "de", logger: Optional[logging.Logger] = None) -> None:
        self.default_language = default_language
        self._global_language: Optional[str] = None
        self._user_languages: Dict[int, str] = {}
        self._translations: Dict[str, Dict[str, Dict[str, str]]] = {}
        self._feature_languages: Dict[str, Set[str]] = {}
        self._supported_languages: Set[str] = {default_language}

        # Logging state (per run)
        self._logged_missing_keys: Set[tuple[str, str]] = set()
        self._logged_duplicate_keys: Set[tuple[str, str]] = set()
        self._logged_empty_translations: Set[tuple[str, str]] = set()
        self._logged_missing_files: Set[str] = set()
        self._logger = logger or logging.getLogger("translation")

    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #

    def _log_once(self, bucket: Set, key, action: str, message: str, *, feature_id: Optional[str] = None) -> None:
        if key in bucket:
            return
        bucket.add(key)
        try:
            self._logger.warning(message, extra={"action": action, "feature_id": feature_id})
        except Exception:
            # Logging must never break translation
            pass

    def _normalize_feature(self, feature_id: str) -> str:
        return (feature_id or "").strip()

    def _normalize_label(self, label: str) -> str:
        return "".join(str(label or "").split())

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #

    def reset(self) -> None:
        """Clear all loaded data (primarily for tests)."""
        self._global_language = None
        self._user_languages.clear()
        self._translations.clear()
        self._feature_languages.clear()
        self._supported_languages = {self.default_language}
        self._logged_missing_keys.clear()
        self._logged_duplicate_keys.clear()
        self._logged_empty_translations.clear()
        self._logged_missing_files.clear()

    def load_features(self, descriptors: Iterable[FeatureDescriptor]) -> None:
        """
        Load labels.tsv for every provided feature descriptor.
        """
        for desc in descriptors:
            feature_id = self._normalize_feature(desc.id)
            labels_path = Path(desc.root_path) / "labels.tsv"

            if not labels_path.exists():
                self._log_once(
                    self._logged_missing_files,
                    feature_id,
                    "I18N_MISSING_KEY",
                    f"labels.tsv missing for feature '{feature_id}'",
                    feature_id=feature_id,
                )
                continue

            try:
                self._load_single_feature(feature_id, labels_path)
            except (OSError, ValueError, UnicodeDecodeError) as exc:
                self._log_once(
                    self._logged_missing_files,
                    feature_id,
                    "I18N_MISSING_KEY",
                    f"Failed to load labels.tsv for '{feature_id}': {exc}",
                    feature_id=feature_id,
                )

    def _load_single_feature(self, feature_id: str, tsv_path: Path) -> None:
        raw_lines = tsv_path.read_text(encoding="utf-8").splitlines()
        lines = [line for line in raw_lines if line.strip() and not line.strip().startswith("#")]
        if not lines:
            return

        header = lines[0].split("\t")
        if len(header) < 2 or header[0].strip().lower() != "label":
            raise ValueError("Invalid TSV header: first column must be 'label' and at least one language column is required")

        languages = [col.strip().lower() for col in header[1:] if col.strip()]
        if not languages:
            languages = [self.default_language]

        feature_store: Dict[str, Dict[str, str]] = {}
        feature_langs: Set[str] = set()

        for row in lines[1:]:
            cols = row.split("\t")
            if not cols:
                continue
            label = self._normalize_label(cols[0])
            if not label:
                continue

            translations: Dict[str, str] = {}
            for idx, lang in enumerate(languages, start=1):
                text = cols[idx] if idx < len(cols) else ""
                translations[lang] = text
                feature_langs.add(lang)
                if not text.strip():
                    self._log_once(
                        self._logged_empty_translations,
                        (feature_id, label),
                        "I18N_EMPTY_TRANSLATION",
                        f"Empty translation for '{label}' in feature '{feature_id}'",
                        feature_id=feature_id,
                    )

            existing = feature_store.get(label)
            if existing and existing != translations:
                self._log_once(
                    self._logged_duplicate_keys,
                    (feature_id, label),
                    "I18N_DUPLICATE_KEY",
                    f"Duplicate key '{label}' in feature '{feature_id}' with differing translations",
                    feature_id=feature_id,
                )

            feature_store[label] = translations

        if feature_store:
            self._translations[feature_id] = feature_store
            self._feature_languages[feature_id] = feature_langs or {self.default_language}
            self._supported_languages.update(feature_langs)
        else:
            self._translations.pop(feature_id, None)
            self._feature_languages.pop(feature_id, None)

    def set_global_language(self, lang: str) -> bool:
        lang_n = (lang or "").strip().lower()
        if lang_n and lang_n in self.available_languages():
            self._global_language = lang_n
            return True
        return False

    def set_user_language(self, user_id: int, lang: str) -> bool:
        lang_n = (lang or "").strip().lower()
        if lang_n and lang_n in self.available_languages():
            self._user_languages[user_id] = lang_n
            return True
        return False

    def get_effective_language(self, user_id: Optional[int]) -> str:
        if user_id is not None:
            user_lang = self._user_languages.get(user_id)
            if user_lang:
                return user_lang
        if self._global_language:
            return self._global_language
        return self.default_language

    def available_languages(self, feature_id: Optional[str] = None) -> list[str]:
        if feature_id:
            feat_norm = self._normalize_feature(feature_id)
            if feat_norm in self._feature_languages:
                langs = self._feature_languages[feat_norm].copy()
                langs.add(self.default_language)
                return sorted(langs)
        return sorted(self._supported_languages | {self.default_language})

    def t(self, key: str, *, feature_id: str, user_id: Optional[int] = None) -> str:
        feature_norm = self._normalize_feature(feature_id)
        label = self._normalize_label(key)
        lang = self.get_effective_language(user_id)

        feature_data = self._translations.get(feature_norm)
        if not feature_data:
            self._log_once(
                self._logged_missing_keys,
                (feature_norm, label),
                "I18N_MISSING_KEY",
                f"Missing translation key '{label}' in feature '{feature_norm}'",
                feature_id=feature_norm,
            )
            return label or key

        translations = feature_data.get(label)
        if translations is None:
            self._log_once(
                self._logged_missing_keys,
                (feature_norm, label),
                "I18N_MISSING_KEY",
                f"Missing translation key '{label}' in feature '{feature_norm}'",
                feature_id=feature_norm,
            )
            return label or key

        text = translations.get(lang, "")
        if not text.strip():
            self._log_once(
                self._logged_empty_translations,
                (feature_norm, label),
                "I18N_EMPTY_TRANSLATION",
                f"Empty or unsupported translation for '{label}' in feature '{feature_norm}'",
                feature_id=feature_norm,
            )
            return label or key

        return text
