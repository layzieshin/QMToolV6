# Authenticator Feature Contract

```json
{
  "feature_id": "authenticator",
  "consumes": [
    {"name": "SessionRepository", "schema_path": "authenticator.repository.session_repository.SessionRepository", "cardinality": "1"},
    {"name": "UserRepository", "schema_path": "user_management.repository.user_repository.UserRepository", "cardinality": "1"},
    {"name": "AuthenticatorPolicy", "schema_path": "authenticator.services.policy.authenticator_policy.AuthenticatorPolicy", "cardinality": "1"},
    {"name": "SQLAlchemy Session", "schema_path": "sqlalchemy.orm.Session", "cardinality": "1"},
    {"name": "bcrypt", "schema_path": "bcrypt", "cardinality": "1"},
    {"name": "shared.database.Base", "schema_path": "shared.database.base.Base", "cardinality": "1"}
  ],
  "produces": [
    {"name": "sessions", "schema_path": "table:sessions (id, session_id, user_id, username, created_at, expires_at, ip_address, user_agent)", "cardinality": "0..*"},
    {"name": "SessionDTO", "schema_path": "authenticator.dto.auth_dto.SessionDTO", "cardinality": "0..*"},
    {"name": "AuthenticationResultDTO", "schema_path": "authenticator.dto.auth_dto.AuthenticationResultDTO", "cardinality": "1"}
  ],
  "side_effects": [
    "db:insert INTO sessions (on successful login)",
    "db:delete FROM sessions (on logout or session cleanup)",
    "session:create (32-byte secure token via secrets.token_urlsafe)"
  ],
  "failure_modes": [
    {"code": "InvalidCredentialsException", "conditions": "Username empty, password empty, or password verification fails", "propagation": "InvalidCredentialsException (wrapped in AuthenticationResultDTO with success=False)"},
    {"code": "SessionNotFoundException", "conditions": "Session ID not found in database", "propagation": "SessionNotFoundException"},
    {"code": "SessionExpiredException", "conditions": "Session exists but expires_at < now() or status is EXPIRED", "propagation": "SessionExpiredException"},
    {"code": "UserNotAuthenticatedException", "conditions": "Session status is INVALID", "propagation": "UserNotAuthenticatedException"},
    {"code": "PasswordHashingException", "conditions": "bcrypt.checkpw() fails with encoding or hashing error", "propagation": "PasswordHashingException"}
  ],
  "auth_rules": [
    {"action": "login", "required_roles": ["*"], "additional_checks": "Username must exist in UserRepository, password must match bcrypt hash"},
    {"action": "logout", "required_roles": ["*"], "additional_checks": "Session ID must exist"},
    {"action": "validate_session", "required_roles": ["*"], "additional_checks": "Session must exist and not be expired/invalid"},
    {"action": "get_session", "required_roles": ["*"], "additional_checks": "Session ID must exist"}
  ],
  "assumptions": [
    "ASSUMPTION: UserRepository from user_management provides get_by_username() returning entity with password_hash field",
    "ASSUMPTION: Session tokens are generated using secrets.token_urlsafe(32) providing 256 bits of entropy",
    "ASSUMPTION: Default session validity is 24 hours (configurable via expires_in_hours)",
    "ASSUMPTION: Password hashing uses bcrypt with automatic salt generation",
    "ASSUMPTION: Session status is computed at query time by comparing expires_at with current timestamp",
    "ASSUMPTION: SQLAlchemy Session is provided via dependency injection",
    "ASSUMPTION: SessionEntity uses shared.database.base.Base as declarative base"
  ]
}
```
