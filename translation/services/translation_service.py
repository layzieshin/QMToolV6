from typing import Optional
from translation.services.translation_service_interface import TranslationServiceInterface
from translation.repository.translation_repository_interface import TranslationRepositoryInterface
from translation.services.policy.translation_policy import TranslationPolicy
from translation.services.feature_discovery_service import FeatureDiscoveryService
from translation.dto.translation_dto import (
    TranslationDTO,
    TranslationSetDTO,
    CreateTranslationDTO,
    UpdateTranslationDTO
)
from translation.enum.language_enum import SupportedLanguage
from translation.exceptions.translation_exceptions import (
    TranslationNotFoundError,
    TranslationAlreadyExistsError
)
from audittrail.services.audit_service_interface import AuditServiceInterface
from audittrail.enum.audit_enum import LogLevel, AuditSeverity, AuditActionType


class TranslationService(TranslationServiceInterface):
    """
    Core translation service implementation.

    Dependencies:
    - TranslationRepository:  Data access
    - TranslationPolicy: Authorization
    - AuditService: Change tracking
    - FeatureDiscoveryService:  Auto-loading
    """

    def __init__(
            self,
            repository: TranslationRepositoryInterface,
            policy: TranslationPolicy,
            audit_service: AuditServiceInterface,
            discovery_service: FeatureDiscoveryService
    ):
        self._repo = repository
        self._policy = policy
        self._audit = audit_service
        self._discovery = discovery_service
        self._missing_logged: set[tuple[str, str, str]] = set()  # (feature, label, lang)

    def get(
            self,
            label: str,
            language: SupportedLanguage,
            feature: str,
            fallback_to_label: bool = True
    ) -> str:
        """
        Get translation with fallback and logging.
        """
        translation = self._repo.get_translation(label, language, feature)

        if translation and translation.text.strip():
            return translation.text

        # Log missing translation (once per label/lang/feature)
        key = (feature, label, language.value)
        if key not in self._missing_logged:
            self._audit.log(
                user_id=0,  # System
                action=AuditActionType.OTHER,
                feature="translation",
                log_level=LogLevel.WARNING,
                severity=AuditSeverity.LOW,
                details={
                    "event": "missing_translation",
                    "label": label,
                    "language": language.value,
                    "feature": feature
                }
            )
            self._missing_logged.add(key)

        return label if fallback_to_label else ""

    def create_translation(
            self,
            dto: CreateTranslationDTO,
            actor_id: int
    ) -> TranslationSetDTO:
        """
        Create new translation set.
        """
        # Policy check
        self._policy.enforce_create(actor_id)

        # Check if exists
        existing = self._repo.get_translation_set(dto.label, dto.feature)
        if existing:
            raise TranslationAlreadyExistsError(
                f"Translation already exists:  {dto.feature}.{dto.label}"
            )

        # Create
        translation_set = TranslationSetDTO(
            label=dto.label,
            feature=dto.feature,
            translations=dto.translations
        )
        self._repo.create_translation_set(translation_set)

        # Audit
        self._audit.log(
            user_id=actor_id,
            action=AuditActionType.CREATE,
            feature="translation",
            log_level=LogLevel.INFO,
            severity=AuditSeverity.INFO,
            details={
                "label": dto.label,
                "feature": dto.feature,
                "languages": list(dto.translations.keys())
            }
        )

        return translation_set

    def update_translation(
            self,
            dto: UpdateTranslationDTO,
            actor_id: int
    ) -> TranslationDTO:
        """
        Update single translation.
        """
        # Policy check
        self._policy.enforce_update(actor_id)

        # Get old value
        old_translation = self._repo.get_translation(dto.label, dto.language, dto.feature)
        if not old_translation:
            raise TranslationNotFoundError(
                f"Translation not found: {dto.feature}.{dto.label}.{dto.language.value}"
            )

        # Update
        self._repo.update_translation(dto.label, dto.feature, dto.language, dto.text)

        # Get updated
        updated = self._repo.get_translation(dto.label, dto.language, dto.feature)

        # Audit
        self._audit.log(
            user_id=actor_id,
            action=AuditActionType.UPDATE,
            feature="translation",
            log_level=LogLevel.INFO,
            severity=AuditSeverity.INFO,
            details={
                "label": dto.label,
                "feature": dto.feature,
                "language": dto.language.value,
                "old_text": old_translation.text,
                "new_text": dto.text
            }
        )

        return updated

    def delete_translation(self, label: str, feature: str, actor_id: int) -> None:
        """
        Delete translation set.
        """
        # Policy check (ADMIN only)
        self._policy.enforce_delete(actor_id)

        # Check exists
        translation_set = self._repo.get_translation_set(label, feature)
        if not translation_set:
            raise TranslationNotFoundError(
                f"Translation set not found: {feature}.{label}"
            )

        # Delete
        self._repo.delete_translation_set(label, feature)

        # Audit (CRITICAL severity)
        self._audit.log(
            user_id=actor_id,
            action=AuditActionType.DELETE,
            feature="translation",
            log_level=LogLevel.WARNING,
            severity=AuditSeverity.CRITICAL,
            details={
                "label": label,
                "feature": feature,
                "deleted_languages": list(translation_set.translations.keys())
            }
        )

    def get_missing_for_feature(self, feature: str) -> list[TranslationSetDTO]:
        """Get translation sets with missing languages."""
        return self._repo.get_missing_translations(feature)

    def get_coverage(self, feature: str) -> dict[SupportedLanguage, float]:
        """
        Calculate coverage per language.
        """
        all_translations = self._repo.get_all_by_feature(feature)
        if not all_translations:
            return {lang: 0.0 for lang in SupportedLanguage}

        total = len(all_translations)
        coverage = {}

        for lang in SupportedLanguage:
            complete_count = sum(
                1 for trans_set in all_translations
                if lang in trans_set.translations and trans_set.translations[lang].strip()
            )
            coverage[lang] = complete_count / total if total > 0 else 0.0

        return coverage

    def load_all_features(self) -> dict[str, int]:
        """
        Auto-discover and load all features.
        """
        discovered = self._discovery.discover_features()
        loaded = {}

        for feature_name, tsv_path in discovered.items():
            try:
                count = self._repo.load_feature_tsv(feature_name, str(tsv_path))
                loaded[feature_name] = count
            except Exception as e:
                # Log error but continue
                self._audit.log(
                    user_id=0,
                    action=AuditActionType.OTHER,
                    feature="translation",
                    log_level=LogLevel.ERROR,
                    severity=AuditSeverity.MEDIUM,
                    details={
                        "event": "load_failed",
                        "feature": feature_name,
                        "error": str(e)
                    }
                )

        return loaded

    def export_feature(
            self,
            feature: str,
            output_path: str,
            format: str = "tsv"
    ) -> None:
        """
        Export feature translations.
        """
        if format == "tsv":
            self._repo.persist_feature_tsv(feature, output_path)
        elif format == "json":
            # TODO: Implement JSON export
            raise NotImplementedError("JSON export not yet implemented")
        elif format == "csv":
            # TODO: Implement CSV export
            raise NotImplementedError("CSV export not yet implemented")
        else:
            raise ValueError(f"Unsupported export format: {format}")