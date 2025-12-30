# AuditTrail Feature Contract

```json
{
  "feature_id": "audittrail",
  "consumes": [
    {"name": "AuditRepository", "schema_path": "audittrail.repository.audit_repository.AuditRepository", "cardinality": "1"},
    {"name": "AuditPolicy", "schema_path": "audittrail.services.policy.audit_policy.AuditPolicy", "cardinality": "1"},
    {"name": "Configurator", "schema_path": "configurator.services.configurator_service.ConfiguratorService", "cardinality": "1"},
    {"name": "SQLite", "schema_path": "sqlite3", "cardinality": "1"}
  ],
  "produces": [
    {"name": "audit_logs", "schema_path": "table:audit_logs (id, timestamp, user_id, username, feature, action, log_level, severity, ip_address, session_id, module, function, details)", "cardinality": "0..*"},
    {"name": "AuditLogDTO", "schema_path": "audittrail.dto.audit_dto.AuditLogDTO", "cardinality": "0..*"},
    {"name": "json_export", "schema_path": "string:JSON array of audit log entries", "cardinality": "0..*"},
    {"name": "csv_export", "schema_path": "string:CSV formatted audit log entries", "cardinality": "0..*"}
  ],
  "side_effects": [
    "db:insert INTO audit_logs",
    "db:delete FROM audit_logs WHERE timestamp < cutoff_date",
    "db:create TABLE audit_logs (if not exists)",
    "db:create INDEX idx_audit_* (if not exists)"
  ],
  "failure_modes": [
    {"code": "AuditAccessDeniedException", "conditions": "User attempts to read logs without permission (not System user 0, not Admin/QMB, and not own logs)", "propagation": "AuditAccessDeniedException"},
    {"code": "FeatureNotFoundException", "conditions": "Feature meta.json not found when loading audit config", "propagation": "FeatureNotFoundException"},
    {"code": "InvalidAuditLogException", "conditions": "CreateAuditLogDTO validation fails (missing user_id, feature, action, or invalid log_level/severity)", "propagation": "InvalidAuditLogException"},
    {"code": "ExportFormatException", "conditions": "Export format is not 'json' or 'csv'", "propagation": "ExportFormatException"},
    {"code": "DatabaseException", "conditions": "SQLite connection or query failure", "propagation": "DatabaseException"}
  ],
  "auth_rules": [
    {"action": "log", "required_roles": ["*"], "additional_checks": "No auth check - any caller can log events"},
    {"action": "get_logs", "required_roles": ["ADMIN", "QMB", "System(0)"], "additional_checks": "Normal users can only read own logs via user_id filter"},
    {"action": "get_user_logs", "required_roles": ["ADMIN", "QMB", "System(0)"], "additional_checks": "Normal users can only read own logs"},
    {"action": "get_feature_logs", "required_roles": ["ADMIN", "QMB", "System(0)"], "additional_checks": "None"},
    {"action": "search_logs", "required_roles": ["ADMIN", "QMB", "System(0)"], "additional_checks": "Respects filter user_id restrictions"},
    {"action": "export_logs", "required_roles": ["ADMIN", "QMB", "System(0)"], "additional_checks": "Must also have read permission for filtered logs"},
    {"action": "delete_old_logs", "required_roles": ["*"], "additional_checks": "No auth check - typically called by system scheduled tasks"},
    {"action": "set_min_log_level", "required_roles": ["*"], "additional_checks": "No auth check - configuration operation"}
  ],
  "assumptions": [
    "ASSUMPTION: SQLite database file is accessible and writable by the process",
    "ASSUMPTION: Configurator provides get_feature_meta() method returning meta.json content",
    "ASSUMPTION: System user (user_id=0) has full access and resolves to username 'SYSTEM'",
    "ASSUMPTION: Admin user IDs are hardcoded as [1] and QMB as [2] in AuditPolicy (placeholder for future UserManagement integration)",
    "ASSUMPTION: Log retention cleanup is triggered externally (scheduler or manual call)",
    "ASSUMPTION: Details field is stored as JSON string in SQLite",
    "ASSUMPTION: Timestamps are stored in ISO 8601 format"
  ]
}
```
