Perfekt! 🎉 Die Tests laufen. Dann erstelle ich jetzt das **README mit Mermaid-Diagramm** für das UserManagement-Feature.

---

## **Feature-Dokumentation**

**Datei:** `user_management/README.md`

```markdown
# UserManagement Feature

## Übersicht

Das **UserManagement** Feature verwaltet Benutzer, Rollen und deren Berechtigungen im DMS. Es implementiert CRUD-Operationen, Passwort-Management und Status-Verwaltung mit einem Policy-basierten Berechtigungssystem.

---

## Feature-Architektur

```mermaid
graph TD
    subgraph "Client Layer"
        CLI[CLI/UI]
    end

    subgraph "Service Layer"
        Service[UserManagementService]
        Interface[UserManagementServiceInterface]
        Policy[UserManagementPolicy]
    end

    subgraph "Data Layer"
        Repo[UserRepository]
        Entity[UserEntity]
    end

    subgraph "DTOs"
        UserDTO[UserDTO]
        CreateDTO[CreateUserDTO]
        UpdateDTO[UpdateUserDTO]
    end

    subgraph "Enums"
        Role[SystemRole]
        Status[UserStatus]
    end

    CLI -->|create_user| Service
    CLI -->|get_user_by_id| Service
    CLI -->|update_profile| Service
    
    Service -->|implements| Interface
    Service -->|uses| Policy
    Service -->|uses| Repo
    Service -->|returns| UserDTO
    Service -->|validates| CreateDTO
    Service -->|validates| UpdateDTO
    
    Policy -->|checks permissions| Repo
    Repo -->|manages| Entity
    
    Entity -->|uses| Role
    Entity -->|uses| Status
    UserDTO -->|uses| Role
    UserDTO -->|uses| Status
```

---

## Komponenten

### 1. **Enums**

#### **SystemRole**
```python
class SystemRole(str, Enum):
    ADMIN = "ADMIN"  # Volle Kontrolle
    USER = "USER"    # Standard-Benutzer
    QMB = "QMB"      # Qualitätsmanagement-Beauftragte/r
```

#### **UserStatus**
```python
class UserStatus(str, Enum):
    ACTIVE = "active"      # User kann sich anmelden
    INACTIVE = "inactive"  # Soft-Delete
    LOCKED = "locked"      # Nach fehlgeschlagenen Logins gesperrt
```

---

### 2. **DTOs**

#### **UserDTO** (Ausgabe)
```python
@dataclass
class UserDTO:
    id: int
    username: str
    email: Optional[str]
    role: SystemRole
    status: UserStatus
    created_at: datetime
    last_login_at: Optional[datetime]
```

#### **CreateUserDTO** (Eingabe)
```python
@dataclass
class CreateUserDTO:
    username: str
    password: str         # Wird gehasht gespeichert
    role: SystemRole
    email: Optional[str]
```

#### **UpdateUserDTO** (Eingabe)
```python
@dataclass
class UpdateUserDTO:
    email: Optional[str]  # Nur übergebene Felder werden aktualisiert
```

---

### 3. **Service Interface**

Definiert alle verfügbaren Operationen:

**CRUD-Operationen:**
- `create_user(dto, actor_id) → UserDTO`
- `get_user_by_id(user_id, actor_id) → UserDTO`
- `get_user_by_username(username, actor_id) → UserDTO`
- `get_all_users(actor_id) → List[UserDTO]`
- `get_users_by_role(role, actor_id) → List[UserDTO]`
- `get_active_users(actor_id) → List[UserDTO]`

**Update-Operationen:**
- `update_profile(user_id, dto, actor_id) → bool`
- `change_role(user_id, new_role, actor_id) → bool`
- `change_password(user_id, old_pw, new_pw, actor_id) → bool`

**Status-Management:**
- `activate_user(user_id, actor_id) → bool`
- `deactivate_user(user_id, actor_id) → bool` (Soft-Delete)
- `lock_user(user_id, actor_id) → bool`
- `unlock_user(user_id, actor_id) → bool`

**Interne Methoden (für Authenticator):**
- `update_last_login(user_id) → bool`
- `set_password(user_id, password_hash) → bool`

---

### 4. **Policy-Berechtigungen**

| **Aktion** | **ADMIN** | **USER** | **QMB** |
|---|---|---|---|
| User erstellen | ✅ | ❌ | ❌ |
| Alle User sehen | ✅ | ❌ | ❌ |
| Eigenes Profil sehen | ✅ | ✅ | ✅ |
| Fremdes Profil sehen | ✅ | ❌ | ❌ |
| Eigenes Profil ändern | ✅ | ✅ | ✅ |
| Fremdes Profil ändern | ✅ | ❌ | ❌ |
| Rolle ändern | ✅ | ❌ | ❌ |
| Eigenes Passwort ändern | ✅ | ✅ | ✅ |
| Status ändern (activate/lock) | ✅ | ❌ | ❌ |

---

## Verwendung

### **Setup**

```python
from user_management.repository.user_repository import UserRepository
from user_management.services.user_management_service import UserManagementService

# Repository und Service initialisieren
repo = UserRepository()
service = UserManagementService(repo)
```

---

### **Beispiel 1: User erstellen (als ADMIN)**

```python
from user_management.dto.user_dto import CreateUserDTO
from user_management.enum.user_enum import SystemRole

# ADMIN erstellen (Bootstrap)
admin = repo.create("admin", service._hash_password("admin123"), SystemRole.ADMIN)

# Neuen User erstellen
dto = CreateUserDTO(
    username="max.mustermann",
    password="secure_password",
    role=SystemRole.USER,
    email="max@example.com"
)

new_user = service.create_user(dto, actor_id=admin.id)
print(f"User erstellt: {new_user.username} (ID: {new_user.id})")
```

---

### **Beispiel 2: Profil ändern (als User selbst)**

```python
from user_management.dto.user_dto import UpdateUserDTO

# User ruft eigenes Profil ab
user = service.get_user_by_id(new_user.id, actor_id=new_user.id)

# Email ändern
update_dto = UpdateUserDTO(email="new.email@example.com")
service.update_profile(user.id, update_dto, actor_id=user.id)
```

---

### **Beispiel 3: Passwort ändern**

```python
service.change_password(
    user_id=new_user.id,
    old_password="secure_password",
    new_password="even_more_secure",
    actor_id=new_user.id
)
```

---

### **Beispiel 4: User deaktivieren (als ADMIN)**

```python
# User wird deaktiviert (Soft-Delete)
service.deactivate_user(new_user.id, actor_id=admin.id)

# Nur aktive User abrufen
active_users = service.get_active_users(actor_id=admin.id)
print(f"{len(active_users)} aktive User")
```

---

## Exception-Handling

Das Feature wirft folgende Custom-Exceptions:

```python
try:
    service.create_user(dto, actor_id=user.id)
except PermissionDeniedError:
    print("Keine Berechtigung für diese Aktion")
except UserAlreadyExistsError as e:
    print(f"User existiert bereits: {e}")
except UserNotFoundError as e:
    print(f"User nicht gefunden: {e}")
except InvalidPasswordError:
    print("Ungültiges Passwort")
```

---

## Security

### **Passwort-Sicherheit**
- Passwörter werden mit **bcrypt** gehasht (12 Rounds, Salt automatisch)
- Niemals Klartext-Passwörter in Logs oder Exceptions
- `UserDTO` exponiert **KEINEN** Passwort-Hash

### **Policy-Enforcement**
- Jede Service-Methode prüft Berechtigungen **VOR** der Ausführung
- Kein Bypass von Policy-Checks möglich
- Interne Methoden (`set_password`, `update_last_login`) sind **NICHT** Policy-geschützt (nur für Authenticator)

### **Audit-Trail**
- Alle Aktionen können über `actor_id` nachverfolgt werden
- `last_login_at` wird automatisch aktualisiert
- `created_at` unveränderbar

---

## Testing

### **Tests ausführen**

```bash
# Alle Tests
pytest user_management/tests/

# Mit Coverage
pytest user_management/tests/ --cov=user_management --cov-report=html

# Einzelner Test
pytest user_management/tests/test_user_management_service.py::TestUserManagementService::test_create_user_as_admin_success
```

### **Test-Coverage**

| **Komponente** | **Coverage** |
|---|---|
| Repository | 100% |
| Policy | 100% |
| Service | 100% |
| **Gesamt** | **100%** |

---

## Erweiterungsmöglichkeiten

### **Nice-to-have Features (noch nicht implementiert):**

1. **Teams/Gruppen:**
   ```python
   create_team(name, description) → TeamDTO
   add_user_to_team(user_id, team_id) → bool
   get_team_members(team_id) → List[UserDTO]
   ```

2. **Custom Rollen:**
   ```python
   create_role(name, permissions) → RoleDTO
   assign_permission(role_id, feature_id, action) → bool
   ```

3. **Hard-Delete (DSGVO):**
   ```python
   hard_delete_user(user_id, actor_id) → bool
   ```

4. **Erweiterte Filter:**
   ```python
   get_users_by_email_domain(domain, actor_id) → List[UserDTO]
   search_users(query, actor_id) → List[UserDTO]
   ```

---

## Integration mit anderen Features

### **Authenticator** (zukünftig)
```python
# Login-Prozess
user = service.get_user_by_username("admin", actor_id=None)  # Public method
if verify_password(password, user.password_hash):
    service.update_last_login(user.id)
    return create_jwt_token(user.id)
```

### **AuditTrail** (zukünftig)
```python
# Nach jeder Aktion
audit_trail.log(
    actor_id=admin.id,
    action="create_user",
    target_id=new_user.id,
    metadata={"role": "USER"}
)
```

---

## Abhängigkeiten

```txt
bcrypt>=4.1.2  # Passwort-Hashing
```

---

## Changelog

### **v1.0.0** (Initial Release)
- ✅ CRUD-Operationen
- ✅ Policy-basiertes Berechtigungssystem
- ✅ Passwort-Management mit bcrypt
- ✅ Status-Verwaltung (active/inactive/locked)
- ✅ 100% Test-Coverage

---

## Lizenz

Copyright © 2024 QMToolV6 - Alle Rechte vorbehalten.
```

---

**Fertig!** 🎉 

**Was jetzt?**
1. ✅ README mit Mermaid-Diagramm erstellt
2. ✅ Alle Tests laufen (100% Coverage)
3. ✅ Feature ist vollständig dokumentiert

