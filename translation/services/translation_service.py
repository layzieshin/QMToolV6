"""
Translation Service Implementation
===================================

Core business logic for translation management.
"""

from typing import Optional, List, Dict, Set, Tuple

from translation.services.translation_service_interface import TranslationServiceInterface
from translation.repository.translation_repository_interface import TranslationRepositoryInterface
from translation.services.feature_discovery_service import FeatureDiscoveryService
from translation.services.policy.translation_policy import TranslationPolicy
from translation.dto.translation_dto import (
    TranslationDTO,
    TranslationSetDTO,
    CreateTranslationDTO,
    UpdateTranslationDTO,
)
from translation.dto.translation_filter_dto import TranslationFilterDTO
from translation.enum.translation_enum import SupportedLanguage
from translation.exceptions.translation_exceptions import (
    TranslationNotFoundError,
    TranslationAlreadyExistsError,
)

# Conditional import for AuditTrail (optional dependency)
try:
    from audittrail.services.audit_service_interface import AuditServiceInterface
    from audittrail.enum.audit_enum import LogLevel, AuditSeverity, AuditActionType

    AUDIT_AVAILABLE = True
except ImportError:
    AUDIT_AVAILABLE = False
    AuditServiceInterface = None  # type: ignore
    LogLevel = None  # type: ignore
    AuditSeverity = None  # type: ignore
    AuditActionType = None  # type:  ignore


class TranslationService(TranslationServiceInterface):
    """
    Core translation service implementation.

    Dependencies:
    -------------
    - TranslationRepository: Data access
    - TranslationPolicy: Authorization
    - AuditService: Change tracking (optional)
    - FeatureDiscoveryService:  Auto-loading

    Usage:
    ------
        >>> from translation.repository.translation_repository import InMemoryTranslationRepository
        >>> from translation.services.policy.translation_policy import TranslationPolicy
        >>> from translation.services.feature_discovery_service import FeatureDiscoveryService

        >>> repo = InMemoryTranslationRepository()
        >>> policy = TranslationPolicy(user_service)
        >>> discovery = FeatureDiscoveryService()
        >>> service = TranslationService(repo, policy, None, discovery)

        >>> service.load_all_features()
        >>> text = service.get("core.save", SupportedLanguage.DE, "core")
        >>> print(text)
        'Speichern'
    """

    def __init__(
            self,
            repository: TranslationRepositoryInterface,
            policy: TranslationPolicy,
            audit_service: Optional[AuditServiceInterface],
            discovery_service: FeatureDiscoveryService
    ):
        """
        Initialize translation service.

        Args:
            repository: Translation data repository
            policy: Authorization policy
            audit_service:  Audit trail service (optional)
            discovery_service: Feature discovery service
        """
        self._repo = repository
        self._policy = policy
        self._audit = audit_service
        self._discovery = discovery_service
        self._missing_logged: Set[Tuple[str, str, str]] = set()  # (feature, label, lang)

    def _log_audit(
            self,
            user_id: int,
            action: str,
            log_level: str,
            severity: str,
            details: dict
    ) -> None:
        """
        Internal helper for audit logging (gracefully handles missing AuditService).

        Args:
            user_id:  Actor user ID
            action: Action type
            log_level: Log level
            severity: Audit severity
            details: Additional details
        """
        if not self._audit or not AUDIT_AVAILABLE:
            return

        try:
            self._audit.log(
                user_id=user_id,
                action=getattr(AuditActionType, action, AuditActionType.OTHER),
                feature="translation",
                log_level=getattr(LogLevel, log_level, LogLevel.INFO),
                severity=getattr(AuditSeverity, severity, AuditSeverity.INFO),
                details=details
            )
        except Exception:
            # Silently fail if audit logging fails (don't break core functionality)
            pass

    def get(
            self,
            label: str,
            language: SupportedLanguage,
            feature: str,
            fallback_to_label: bool = True
    ) -> str:
        """Get translation text with fallback and logging."""
        translation = self._repo.get_translation(label, language, feature)

        if translation and translation.text.strip():
            return translation.text

        # Log missing translation (once per label/lang/feature)
        key = (feature, label, language.value)
        if key not in self._missing_logged:
            self._log_audit(
                user_id=0,  # System
                action="OTHER",
                log_level="WARNING",
                severity="LOW",
                details={
                    "event": "missing_translation",
                    "label": label,
                    "language": language.value,
                    "feature": feature
                }
            )
            self._missing_logged.add(key)

        return label if fallback_to_label else ""

    def get_translation(
            self,
            label: str,
            language: SupportedLanguage,
            feature: str
    ) -> Optional[TranslationDTO]:
        """Get full TranslationDTO."""
        return self._repo.get_translation(label, language, feature)

    def get_translation_set(self, label: str, feature: str) -> Optional[TranslationSetDTO]:
        """Get complete translation set."""
        return self._repo.get_translation_set(label, feature)

    def query_translations(self, filter_dto: TranslationFilterDTO) -> List[TranslationSetDTO]:
        """
        Query translations with filter criteria.

        Applies filtering based on:
        - feature
        - language (filters sets that have this language)
        - status
        - search_text (in labels)
        - only_missing
        """
        # Get base set
        if filter_dto.feature:
            translation_sets = self._repo.get_all_by_feature(filter_dto.feature)
        else:
            # Get all features
            all_sets = []
            for feature_name in self._repo.get_all_features():
                all_sets.extend(self._repo.get_all_by_feature(feature_name))
            translation_sets = all_sets

        # Apply filters
        results = []
        for trans_set in translation_sets:
            # Language filter (must have translation for this language)
            if filter_dto.language:
                if filter_dto.language not in trans_set.translations:
                    continue

            # Status filter
            if filter_dto.status:
                # Check if any language matches status
                has_status = False
                for lang in SupportedLanguage:
                    text = trans_set.translations.get(lang, "")
                    if filter_dto.status.value == "missing" and not text.strip():
                        has_status = True
                        break
                    elif filter_dto.status.value == "complete" and text.strip():
                        has_status = True
                        break
                if not has_status:
                    continue

            # Search text filter
            if filter_dto.search_text:
                search_lower = filter_dto.search_text.lower()
                if search_lower not in trans_set.label.lower():
                    # Also search in translation texts
                    found_in_text = any(
                        search_lower in text.lower()
                        for text in trans_set.translations.values()
                    )
                    if not found_in_text:
                        continue

            # Only missing filter
            if filter_dto.only_missing:
                if not trans_set.get_missing_languages():
                    continue

            results.append(trans_set)

        return results

    def create_translation(
            self,
            dto: CreateTranslationDTO,
            actor_id: int
    ) -> TranslationSetDTO:
        """Create new translation set."""
        # Policy check
        self._policy.enforce_create(actor_id)

        # Check if exists
        existing = self._repo.get_translation_set(dto.label, dto.feature)
        if existing:
            raise TranslationAlreadyExistsError(
                f"Translation already exists: {dto.feature}. {dto.label}"
            )

        # Create
        translation_set = TranslationSetDTO(
            label=dto.label,
            feature=dto.feature,
            translations=dto.translations
        )
        self._repo.create_translation_set(translation_set)

        # Audit
        self._log_audit(
            user_id=actor_id,
            action="CREATE",
            log_level="INFO",
            severity="INFO",
            details={
                "label": dto.label,
                "feature": dto.feature,
                "languages": [lang.value for lang in dto.translations.keys()]
            }
        )

        return translation_set

    def update_translation(
            self,
            dto: UpdateTranslationDTO,
            actor_id: int
    ) -> TranslationDTO:
        """Update single translation."""
        # Policy check
        self._policy.enforce_update(actor_id)

        # Get old value
        old_translation = self._repo.get_translation(dto.label, dto.language, dto.feature)
        if not old_translation:
            raise TranslationNotFoundError(
                f"Translation not found: {dto.feature}.{dto.label}. {dto.language.value}"
            )

        # Update
        self._repo.update_translation(dto.label, dto.feature, dto.language, dto.text)

        # Get updated
        updated = self._repo.get_translation(dto.label, dto.language, dto.feature)

        # Audit
        self._log_audit(
            user_id=actor_id,
            action="UPDATE",
            log_level="INFO",
            severity="INFO",
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
        """Delete translation set."""
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
        self._log_audit(
            user_id=actor_id,
            action="DELETE",
            log_level="WARNING",
            severity="CRITICAL",
            details={
                "label": label,
                "feature": feature,
                "deleted_languages": [lang.value for lang in translation_set.translations.keys()]
            }
        )

    def get_missing_for_feature(self, feature: str) -> List[TranslationSetDTO]:
        """Get translation sets with missing languages."""
        return self._repo.get_missing_translations(feature)

    def get_coverage(self, feature: str) -> Dict[SupportedLanguage, float]:
        """Calculate coverage per language."""
        return self._repo.get_coverage(feature)

    def get_all_features(self) -> List[str]:
        """Get list of all loaded features."""
        return self._repo.get_all_features()

    def load_all_features(self) -> Dict[str, int]:
        """
        Auto-discover and load all features.

        Logs errors but continues loading other features.
        """
        discovered = self._discovery.discover_features()
        loaded = {}

        for feature_name, tsv_path in discovered.items():
            try:
                count = self._repo.load_feature_tsv(feature_name, str(tsv_path))
                loaded[feature_name] = count

                # Audit successful load
                self._log_audit(
                    user_id=0,  # System
                    action="OTHER",
                    log_level="INFO",
                    severity="INFO",
                    details={
                        "event": "feature_loaded",
                        "feature": feature_name,
                        "count": count,
                        "path": str(tsv_path)
                    }
                )
            except Exception as e:
                # Log error but continue
                self._log_audit(
                    user_id=0,
                    action="OTHER",
                    log_level="ERROR",
                    severity="MEDIUM",
                    details={
                        "event": "load_failed",
                        "feature": feature_name,
                        "error": str(e),
                        "path": str(tsv_path)
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

        Currently only TSV format is implemented.
        """
        if format == "tsv":
            self._repo.persist_feature_tsv(feature, output_path)
        elif format == "json":
            self._export_json(feature, output_path)
        elif format == "csv":
            self._export_csv(feature, output_path)
        else:
            raise ValueError(f"Unsupported export format: {format}.  Supported: tsv, json, csv")

    def _export_json(self, feature: str, output_path: str) -> None:
        """Export translations as JSON."""
        import json
        from pathlib import Path

        translation_sets = self._repo.get_all_by_feature(feature)

        # Convert to JSON-serializable format
        data = {
            "feature": feature,
            "translations": []
        }

        for trans_set in translation_sets:
            data["translations"].append({
                "label": trans_set.label,
                "texts": {lang.value: text for lang, text in trans_set.translations.items()}
            })

        # Write with pretty formatting
        Path(output_path).write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    def _export_csv(self, feature: str, output_path: str) -> None:
        """Export translations as CSV (Excel-compatible)."""
        import csv
        from pathlib import Path

        translation_sets = self._repo.get_all_by_feature(feature)

        with Path(output_path).open("w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)

            # Write header
            writer.writerow(["label"] + SupportedLanguage.all_codes())

            # Write rows
            for trans_set in sorted(translation_sets, key=lambda x: x.label):
                row = [trans_set.label]
                for lang in SupportedLanguage:
                    row.append(trans_set.translations.get(lang, ""))
                writer.writerow(row)