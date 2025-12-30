# UserManagement Feature Contract

```json
{
  "feature_id": "user_management",
  "consumes": [
    {"name": "UserRepository", "schema_path": "user_management.repository.user_repository.UserRepository", "cardinality": "1"},
    {"name": "UserManagementPolicy", "schema_path": "user_management.services.policy.user_management_policy.UserManagementPolicy", "cardinality": "1"},
    {"name": "bcrypt", "schema_path": "bcrypt", "cardinality": "1"}
  ],
  "produces": [
    {"name": "UserEntity", "schema_path": "user_management.repository.user_repository.UserEntity (in-memory)", "cardinality": "0..*"},
    {"name": "UserDTO", "schema_path": "user_management.dto.user_dto.UserDTO", "cardinality": "0..*"},
    {"name": "users_in_memory", "schema_path": "Dict[int, UserEntity] (id -> entity mapping)", "cardinality": "0..*"}
  ],
  "side_effects": [
    "memory:create UserEntity in _users dict",
    "memory:update UserEntity fields (email, role, status, password_hash, last_login_at)",
    "memory:delete UserEntity from _users dict (hard delete)",
    "hash:bcrypt password hashing with automatic salt"
  ],
  "failure_modes": [
    {"code": "UserNotFoundError", "conditions": "get_user_by_id() or get_user_by_username() called with non-existent user", "propagation": "UserNotFoundError"},
    {"code": "UserAlreadyExistsError", "conditions": "create_user() called with existing username", "propagation": "UserAlreadyExistsError"},
    {"code": "PermissionDeniedError", "conditions": "Actor lacks permission for requested action based on role and policy", "propagation": "PermissionDeniedError"},
    {"code": "InvalidPasswordError", "conditions": "change_password() called with incorrect old_password", "propagation": "InvalidPasswordError"}
  ],
  "auth_rules": [
    {"action": "create_user", "required_roles": ["ADMIN"], "additional_checks": "Only ADMIN can create new users"},
    {"action": "get_user_by_id", "required_roles": ["ADMIN", "USER", "QMB"], "additional_checks": "ADMIN can view all; USER/QMB can only view own profile"},
    {"action": "get_user_by_username", "required_roles": ["ADMIN", "USER", "QMB"], "additional_checks": "ADMIN can view all; USER/QMB can only view own profile"},
    {"action": "get_all_users", "required_roles": ["ADMIN"], "additional_checks": "Only ADMIN can list all users"},
    {"action": "get_users_by_role", "required_roles": ["ADMIN"], "additional_checks": "Only ADMIN can filter users by role"},
    {"action": "get_active_users", "required_roles": ["ADMIN"], "additional_checks": "Only ADMIN can list active users"},
    {"action": "update_profile", "required_roles": ["ADMIN", "USER", "QMB"], "additional_checks": "ADMIN can update all; USER/QMB can only update own profile"},
    {"action": "change_role", "required_roles": ["ADMIN"], "additional_checks": "Only ADMIN can change user roles"},
    {"action": "change_password", "required_roles": ["*"], "additional_checks": "User can only change own password; old_password must match"},
    {"action": "activate_user", "required_roles": ["ADMIN"], "additional_checks": "Only ADMIN can activate users"},
    {"action": "deactivate_user", "required_roles": ["ADMIN"], "additional_checks": "Only ADMIN can deactivate users (soft delete)"},
    {"action": "lock_user", "required_roles": ["ADMIN"], "additional_checks": "Only ADMIN can lock users"},
    {"action": "unlock_user", "required_roles": ["ADMIN"], "additional_checks": "Only ADMIN can unlock users"},
    {"action": "update_last_login", "required_roles": ["*"], "additional_checks": "No policy check - internal method for Authenticator"},
    {"action": "set_password", "required_roles": ["*"], "additional_checks": "No policy check - internal method for Authenticator"}
  ],
  "assumptions": [
    "ASSUMPTION: UserRepository is in-memory (Dict-based); production should use SQLAlchemy with database feature",
    "ASSUMPTION: Passwords are hashed using bcrypt with automatic salt generation",
    "ASSUMPTION: UserDTO does NOT expose password_hash for security reasons",
    "ASSUMPTION: SystemRole enum has values: ADMIN, USER, QMB",
    "ASSUMPTION: UserStatus enum has values: ACTIVE, INACTIVE, LOCKED",
    "ASSUMPTION: New users are created with status=ACTIVE by default",
    "ASSUMPTION: update_last_login() and set_password() are internal methods without policy checks (for Authenticator integration)",
    "ASSUMPTION: Actor's role is determined by looking up actor_id in repository",
    "ASSUMPTION: Thread-safety is NOT implemented in UserRepository (production should use DB transactions or locks)",
    "ASSUMPTION: Hard delete (repository.delete()) available for GDPR compliance but not exposed in service API"
  ]
}
```
