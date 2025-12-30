# Database Core Feature Contract

```json
{
  "feature_id": "database",
  "consumes": [
    {"name": "SQLAlchemy", "schema_path": "sqlalchemy (Engine, Session, scoped_session, sessionmaker)", "cardinality": "1"},
    {"name": "sqlite3", "schema_path": "sqlite3", "cardinality": "1"},
    {"name": "threading", "schema_path": "threading", "cardinality": "1"},
    {"name": "Base", "schema_path": "database.models.base.Base (DeclarativeMeta)", "cardinality": "1"}
  ],
  "produces": [
    {"name": "DatabaseService", "schema_path": "database.logic.services.database_service.DatabaseService", "cardinality": "1"},
    {"name": "UnitOfWork", "schema_path": "database.logic.services.unit_of_work.UnitOfWork", "cardinality": "0..*"},
    {"name": "BaseRepository", "schema_path": "database.logic.repository.base_repository.BaseRepository", "cardinality": "0..*"},
    {"name": "SchemaRegistry", "schema_path": "database.logic.services.schema_registry.SchemaRegistry", "cardinality": "1"},
    {"name": "ConnectionInfoDTO", "schema_path": "database.logic.dto.connection_info_dto.ConnectionInfoDTO", "cardinality": "1"},
    {"name": "Session", "schema_path": "sqlalchemy.orm.Session (thread-local via scoped_session)", "cardinality": "0..*"},
    {"name": "sqlite3.Connection", "schema_path": "sqlite3.Connection (thread-local for legacy code)", "cardinality": "0..*"}
  ],
  "side_effects": [
    "db:create SQLite database file (if not exists)",
    "db:create tables via Base.metadata.create_all()",
    "db:commit (automatic on UnitOfWork context exit)",
    "db:rollback (automatic on exception within UnitOfWork)",
    "memory:thread-local session storage via scoped_session",
    "memory:thread-local connection storage via threading.local()"
  ],
  "failure_modes": [
    {"code": "ConnectionException", "conditions": "Database connection fails during initialization or get_connection()", "propagation": "ConnectionException"},
    {"code": "SessionException", "conditions": "Session cannot be created or database not initialized", "propagation": "SessionException"},
    {"code": "SchemaException", "conditions": "Schema creation fails or schema registry not initialized", "propagation": "SchemaException"},
    {"code": "UnitOfWorkException", "conditions": "UnitOfWork fails during creation or execution", "propagation": "UnitOfWorkException"},
    {"code": "CommitException", "conditions": "Transaction commit fails", "propagation": "CommitException"},
    {"code": "RollbackException", "conditions": "Transaction rollback fails", "propagation": "RollbackException"},
    {"code": "RepositoryException", "conditions": "CRUD operation fails in BaseRepository", "propagation": "RepositoryException"}
  ],
  "auth_rules": [
    {"action": "get_session", "required_roles": ["*"], "additional_checks": "No auth - infrastructure service"},
    {"action": "get_connection", "required_roles": ["*"], "additional_checks": "No auth - only supports SQLite"},
    {"action": "unit_of_work", "required_roles": ["*"], "additional_checks": "No auth - transaction management"},
    {"action": "ensure_schema", "required_roles": ["*"], "additional_checks": "No auth - typically called at startup"},
    {"action": "close", "required_roles": ["*"], "additional_checks": "No auth - cleanup on shutdown"}
  ],
  "assumptions": [
    "ASSUMPTION: Default database URL is 'sqlite:///qmtool.db'",
    "ASSUMPTION: SQLite-specific connect_args with check_same_thread=False for multi-threading",
    "ASSUMPTION: scoped_session provides thread-local Session isolation",
    "ASSUMPTION: UnitOfWork auto-commits on successful context exit (auto_commit=True by default)",
    "ASSUMPTION: UnitOfWork auto-rolls back on exception",
    "ASSUMPTION: BaseRepository uses flush() to get IDs without full commit",
    "ASSUMPTION: Legacy code uses get_connection() for raw sqlite3.Connection access",
    "ASSUMPTION: All ORM entities must inherit from database.models.base.Base",
    "ASSUMPTION: echo=False by default (no SQL statement logging)"
  ]
}
```
