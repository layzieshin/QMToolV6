# Translation Feature Contract

```json
{
  "feature_id": "translation",
  "consumes": [
    {"name": "InMemoryTranslationRepository", "schema_path": "translation.repository.translation_repository.InMemoryTranslationRepository", "cardinality": "1"},
    {"name": "TSVTranslationRepository", "schema_path": "translation.repository.translation_repository.TSVTranslationRepository", "cardinality": "0..1"},
    {"name": "TranslationPolicy", "schema_path": "translation.services.policy.translation_policy.TranslationPolicy", "cardinality": "1"},
    {"name": "FeatureDiscoveryService", "schema_path": "translation.services.feature_discovery_service.FeatureDiscoveryService", "cardinality": "0..1"},
    {"name": "Filesystem", "schema_path": "<feature>/labels.tsv per feature folder", "cardinality": "0..*"},
    {"name": "csv", "schema_path": "csv", "cardinality": "1"},
    {"name": "json", "schema_path": "json", "cardinality": "1"}
  ],
  "produces": [
    {"name": "TranslationDTO", "schema_path": "translation.dto.translation_dto.TranslationDTO", "cardinality": "0..*"},
    {"name": "TranslationSetDTO", "schema_path": "translation.dto.translation_dto.TranslationSetDTO", "cardinality": "0..*"},
    {"name": "tsv_export", "schema_path": "file:TSV formatted translation entries", "cardinality": "0..*"},
    {"name": "csv_export", "schema_path": "file:CSV formatted translation entries", "cardinality": "0..*"},
    {"name": "json_export", "schema_path": "file:JSON array of translation sets", "cardinality": "0..*"},
    {"name": "coverage_stats", "schema_path": "Dict[SupportedLanguage, float] (0.0-1.0 per language)", "cardinality": "0..*"}
  ],
  "side_effects": [
    "fs:read <feature>/labels.tsv for each discovered feature",
    "fs:write <output_path>.tsv (on export or auto-persist)",
    "fs:write <output_path>.csv (on CSV export)",
    "fs:write <output_path>.json (on JSON export)",
    "memory:store translations in _store Dict[(feature, label), TranslationSetDTO]"
  ],
  "failure_modes": [
    {"code": "TranslationNotFoundError", "conditions": "get_translation_set() or update_translation() called with non-existent label/feature", "propagation": "TranslationNotFoundError"},
    {"code": "TranslationAlreadyExistsError", "conditions": "create_translation_set() called with existing label/feature combination", "propagation": "TranslationAlreadyExistsError"},
    {"code": "TranslationPermissionError", "conditions": "User lacks permission for create/update/delete operation", "propagation": "TranslationPermissionError"},
    {"code": "TranslationValidationError", "conditions": "Empty label, invalid language code, or malformed translation data", "propagation": "TranslationValidationError"},
    {"code": "TranslationLoadError", "conditions": "TSV file not found, invalid TSV header, file read/write error, or invalid export format", "propagation": "TranslationLoadError"},
    {"code": "InvalidLanguageError", "conditions": "Unsupported language code in TSV header or from_string()", "propagation": "InvalidLanguageError"}
  ],
  "auth_rules": [
    {"action": "get_translation", "required_roles": ["USER", "ADMIN", "QMB"], "additional_checks": "Policy.enforce_view() if user provided"},
    {"action": "get_translation_dto", "required_roles": ["USER", "ADMIN", "QMB"], "additional_checks": "Policy.enforce_view() if user provided"},
    {"action": "get_translation_set", "required_roles": ["USER", "ADMIN", "QMB"], "additional_checks": "Policy.enforce_view() if user provided"},
    {"action": "query_by_feature", "required_roles": ["USER", "ADMIN", "QMB"], "additional_checks": "Policy.enforce_view() if user provided"},
    {"action": "get_missing_for_feature", "required_roles": ["USER", "ADMIN", "QMB"], "additional_checks": "Policy.enforce_view() if user provided"},
    {"action": "get_coverage", "required_roles": ["USER", "ADMIN", "QMB"], "additional_checks": "Policy.enforce_view() if user provided"},
    {"action": "get_all_features", "required_roles": ["USER", "ADMIN", "QMB"], "additional_checks": "Policy.enforce_view() if user provided"},
    {"action": "create_translation_set", "required_roles": ["ADMIN", "QMB"], "additional_checks": "Policy.enforce_create()"},
    {"action": "update_translation", "required_roles": ["ADMIN", "QMB"], "additional_checks": "Policy.enforce_update()"},
    {"action": "delete_translation_set", "required_roles": ["ADMIN"], "additional_checks": "Policy.enforce_delete()"},
    {"action": "load_all_features", "required_roles": ["*"], "additional_checks": "No auth - typically called at startup"},
    {"action": "export_feature", "required_roles": ["*"], "additional_checks": "No auth - export operation"}
  ],
  "assumptions": [
    "ASSUMPTION: Supported languages are DE (German) and EN (English) defined in SupportedLanguage enum",
    "ASSUMPTION: TSV file format: header 'label\\tde\\ten', rows 'key\\tGerman text\\tEnglish text'",
    "ASSUMPTION: Labels are normalized by removing all whitespace (e.g., 'core. save' -> 'core.save')",
    "ASSUMPTION: Features are normalized by stripping whitespace",
    "ASSUMPTION: fallback_to_de=True returns German translation when requested language is missing",
    "ASSUMPTION: TranslationStatus is MISSING if text is empty or whitespace-only, COMPLETE otherwise",
    "ASSUMPTION: InMemoryTranslationRepository preloads sample data for 'core' feature (core.save, core.cancel, core.missing)",
    "ASSUMPTION: TSVTranslationRepository with auto_persist=True writes to TSV file on every create/update/delete",
    "ASSUMPTION: Export uses atomic temp file write with .tmp extension then rename",
    "ASSUMPTION: TranslationDTO and TranslationSetDTO are frozen dataclasses (immutable)"
  ]
}
```
