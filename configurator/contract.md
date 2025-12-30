# Configurator Feature Contract

```json
{
  "feature_id": "configurator",
  "consumes": [
    {"name": "FeatureRepository", "schema_path": "configurator.repository.feature_repository.FeatureRepository", "cardinality": "1"},
    {"name": "ConfigRepository", "schema_path": "configurator.repository.config_repository.ConfigRepository", "cardinality": "1"},
    {"name": "Filesystem", "schema_path": "features_root (configurable), config/app_config.json", "cardinality": "1"},
    {"name": "json", "schema_path": "json", "cardinality": "1"},
    {"name": "pathlib.Path", "schema_path": "pathlib", "cardinality": "1"}
  ],
  "produces": [
    {"name": "FeatureDescriptorDTO", "schema_path": "configurator.dto.feature_descriptor_dto.FeatureDescriptorDTO", "cardinality": "0..*"},
    {"name": "FeatureRegistryDTO", "schema_path": "configurator.dto.feature_registry_dto.FeatureRegistryDTO", "cardinality": "0..*"},
    {"name": "AppConfigDTO", "schema_path": "configurator.dto.app_config_dto.AppConfigDTO", "cardinality": "1"},
    {"name": "AuditConfigDTO", "schema_path": "configurator.dto.audit_config_dto.AuditConfigDTO", "cardinality": "0..*"}
  ],
  "side_effects": [
    "fs:read <feature_id>/meta.json for each feature folder",
    "fs:read config/app_config.json (if exists)",
    "memory:cache FeatureDescriptorDTO per feature_id"
  ],
  "failure_modes": [
    {"code": "FeatureNotFoundException", "conditions": "Feature folder or meta.json does not exist", "propagation": "FeatureNotFoundException"},
    {"code": "InvalidMetaException", "conditions": "meta.json has invalid JSON, missing required fields (id, label, version, main_class), ID mismatch with folder name, invalid version format, or invalid audit config", "propagation": "InvalidMetaException"},
    {"code": "ConfigValidationException", "conditions": "app_config.json has invalid JSON, invalid values (negative session_timeout, invalid log_level), or validation fails", "propagation": "ConfigValidationException (only in strict mode)"}
  ],
  "auth_rules": [
    {"action": "discover_features", "required_roles": ["*"], "additional_checks": "No auth - read-only operation"},
    {"action": "get_feature_meta", "required_roles": ["*"], "additional_checks": "No auth - read-only operation"},
    {"action": "get_all_features", "required_roles": ["*"], "additional_checks": "Results filtered by visible_for based on caller's role"},
    {"action": "validate_meta", "required_roles": ["*"], "additional_checks": "No auth - validation operation"},
    {"action": "get_app_config", "required_roles": ["*"], "additional_checks": "No auth - read-only operation"}
  ],
  "assumptions": [
    "ASSUMPTION: Feature folders are direct children of features_root directory",
    "ASSUMPTION: Each feature folder contains a meta.json file with required fields: id, label, version, main_class",
    "ASSUMPTION: meta.json id field MUST match the folder name exactly (case-sensitive)",
    "ASSUMPTION: version field follows semantic versioning format X.Y.Z",
    "ASSUMPTION: Ignored folders: shared, .idea, .venv, venv, __pycache__, .pytest_cache, tests, .git, docs, htmlcov, config, data, temp",
    "ASSUMPTION: strict_mode=True causes immediate exception on invalid meta.json; strict_mode=False skips invalid features",
    "ASSUMPTION: app_config.json uses nested structure with database, audit, session, paths sections",
    "ASSUMPTION: AppConfigDTO provides sensible defaults when config file is missing or partially invalid"
  ]
}
```
