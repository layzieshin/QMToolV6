from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Optional, List

from translation.dto.translation_dto import TranslationDTO, TranslationSetDTO
from translation.enum.translation_enum import SupportedLanguage
from translation.exceptions.translation_exceptions import (
    TranslationAlreadyExistsError,
    TranslationNotFoundError,
    TranslationLoadError,
)
from translation.repository.translation_repository import InMemoryTranslationRepository
from translation.services.feature_discovery_service import FeatureDiscoveryService
from translation.services.policy.translation_policy import TranslationPolicy


class TranslationService:
    """
    Service layer for translation operations.

    Tests expect:
      TranslationService(
        repository=...,
        policy=...,
        feature_discovery_service=...
      )

    Your previous __init__ likely used a different parameter name.
    This implementation supports both.
    """

    def __init__(
        self,
        repository: InMemoryTranslationRepository,
        policy: TranslationPolicy,
        feature_discovery_service: Optional[FeatureDiscoveryService] = None,
        discovery_service: Optional[FeatureDiscoveryService] = None,
    ) -> None:
        self._repository = repository
        self._policy = policy
        self._feature_discovery = feature_discovery_service or discovery_service

    # ---------------------------------------------------------------------
    # Reads
    # ---------------------------------------------------------------------

    def get_translation(
        self,
        label: str,
        language: SupportedLanguage,
        feature: str,
        *,
        fallback_to_de: bool = True,
        user=None,
    ) -> Optional[str]:
        """
        Returns the translation text. If missing and fallback enabled, uses DE.
        """
        # policy check: "view" translations requires authenticated user (depending on policy)
        if user is not None and hasattr(self._policy, "enforce_view"):
            self._policy.enforce_view(user)

        dto = self._repository.get_translation(label, language, feature)
        if dto and dto.text.strip():
            return dto.text

        if fallback_to_de and language != SupportedLanguage.DE:
            dto_de = self._repository.get_translation(label, SupportedLanguage.DE, feature)
            if dto_de and dto_de.text.strip():
                return dto_de.text

        return dto.text if dto else None

    def get_translation_dto(
        self,
        label: str,
        language: SupportedLanguage,
        feature: str,
        *,
        user=None,
    ) -> Optional[TranslationDTO]:
        if user is not None and hasattr(self._policy, "enforce_view"):
            self._policy.enforce_view(user)
        return self._repository.get_translation(label, language, feature)

    def get_translation_set(self, label: str, feature: str, *, user=None) -> Optional[TranslationSetDTO]:
        if user is not None and hasattr(self._policy, "enforce_view"):
            self._policy.enforce_view(user)
        return self._repository.get_translation_set(label, feature)

    def query_by_feature(self, feature: str, *, user=None) -> List[TranslationSetDTO]:
        if user is not None and hasattr(self._policy, "enforce_view"):
            self._policy.enforce_view(user)
        return self._repository.get_all_by_feature(feature)

    def get_missing_for_feature(self, feature: str, *, user=None) -> List[TranslationSetDTO]:
        if user is not None and hasattr(self._policy, "enforce_view"):
            self._policy.enforce_view(user)
        return self._repository.get_missing_translations(feature)

    def get_coverage(self, feature: str, *, user=None):
        if user is not None and hasattr(self._policy, "enforce_view"):
            self._policy.enforce_view(user)
        return self._repository.get_coverage(feature)

    def get_all_features(self, *, user=None) -> List[str]:
        if user is not None and hasattr(self._policy, "enforce_view"):
            self._policy.enforce_view(user)
        return self._repository.get_all_features()

    # ---------------------------------------------------------------------
    # Writes
    # ---------------------------------------------------------------------

    def create_translation_set(self, translation_set: TranslationSetDTO, *, user) -> None:
        if hasattr(self._policy, "enforce_create"):
            self._policy.enforce_create(user)
        self._repository.create_translation_set(translation_set)

    def update_translation(self, label: str, feature: str, language: SupportedLanguage, text: str, *, user) -> None:
        if hasattr(self._policy, "enforce_update"):
            self._policy.enforce_update(user)
        self._repository.update_translation(label, feature, language, text)

    def delete_translation_set(self, label: str, feature: str, *, user) -> None:
        if hasattr(self._policy, "enforce_delete"):
            self._policy.enforce_delete(user)
        self._repository.delete_translation_set(label, feature)

    # ---------------------------------------------------------------------
    # Feature loading
    # ---------------------------------------------------------------------

    def load_all_features(self) -> int:
        """
        Load all discovered features. Returns total loaded entries.
        """
        if not self._feature_discovery:
            return 0

        total = 0
        for feat_name, tsv_path in self._feature_discovery.discover_features():
            if not tsv_path:
                continue
            total += self._repository.load_feature_tsv(feat_name, tsv_path)
        return total

    # ---------------------------------------------------------------------
    # Export
    # ---------------------------------------------------------------------

    def export_feature(self, feature: str, out_path: str, fmt: str) -> None:
        """
        Export a feature to TSV / CSV / JSON.
        """
        fmt_n = fmt.strip().lower()
        sets = self._repository.get_all_by_feature(feature)

        if fmt_n == "tsv":
            self._repository.persist_feature_tsv(feature, out_path)
            return

        if fmt_n == "csv":
            self._export_csv(sets, out_path)
            return

        if fmt_n == "json":
            self._export_json(sets, out_path)
            return

        raise TranslationLoadError("Invalid export format")

    def _export_json(self, sets: List[TranslationSetDTO], out_path: str) -> None:
        payload = []
        for ts in sets:
            payload.append(
                {
                    "label": ts.label,
                    "feature": ts.feature,
                    "translations": {str(k): v for k, v in ts.translations.items()},
                }
            )
        Path(out_path).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def _export_csv(self, sets: List[TranslationSetDTO], out_path: str) -> None:
        languages = list(SupportedLanguage)
        header = ["label"] + [str(l) for l in languages]

        p = Path(out_path)
        p.parent.mkdir(parents=True, exist_ok=True)

        with p.open("w", encoding="utf-8", newline="") as f:
            w = csv.writer(f)
            w.writerow(header)
            for ts in sorted(sets, key=lambda x: x.label):
                w.writerow([ts.label] + [ts.translations.get(lang, "") for lang in languages])
