"""UI service layer integrating core services."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, List

import bcrypt

from authenticator.dto.auth_dto import LoginRequestDTO, AuthenticationResultDTO
from audittrail.dto.audit_dto import AuditLogFilterDTO, AuditLogDTO
from audittrail.enum.audit_enum import AuditSeverity, LogLevel
from core.loader import Loader
from core.loader.loader import (
    KEY_AUTH_SERVICE,
    KEY_USER_SERVICE,
    KEY_USER_REPOSITORY,
    KEY_AUDIT_SERVICE,
    KEY_CONFIGURATOR_SERVICE,
)
from user_management.dto.user_dto import CreateUserDTO
from user_management.enum.user_enum import SystemRole

from UI.dto.ui_dto import UILoginDTO, UIRegisterDTO, CreateUIEventDTO, UIEventDTO
from UI.enum.ui_enum import UIAction
from UI.exceptions.ui_exceptions import UIAuthenticationError, UIValidationError
from UI.repository.ui_repository import UIEventRepository
from UI.services.policy.ui_policy import UIPolicy
from UI.services.ui_metadata_service import UIMetadataService


@dataclass
class UIContext:
    """Holds the current UI session state."""

    session_id: Optional[str] = None
    user_id: Optional[int] = None
    username: Optional[str] = None


class UIAppService:
    """Facade for the GUI to access core services."""

    def __init__(
        self,
        auth_service,
        user_service,
        user_repository,
        audit_service,
        metadata_service: UIMetadataService,
        ui_repository: UIEventRepository,
    ) -> None:
        self._auth_service = auth_service
        self._user_service = user_service
        self._user_repository = user_repository
        self._audit_service = audit_service
        self._metadata_service = metadata_service
        self._ui_repository = ui_repository
        self._context = UIContext()
        self._admin_id = self._ensure_admin_user()

    @classmethod
    def from_loader(
        cls,
        project_root: Path,
        config_path: Optional[str] = None,
        ui_db_path: Optional[str] = None,
        labels_path: Optional[Path] = None,
    ) -> "UIAppService":
        loader = Loader(config_path=config_path, project_root=project_root)
        loader.boot()
        container = loader.get_container()
        auth_service = container.resolve(KEY_AUTH_SERVICE)
        user_service = container.resolve(KEY_USER_SERVICE)
        user_repository = container.resolve(KEY_USER_REPOSITORY)
        audit_service = container.resolve(KEY_AUDIT_SERVICE)
        configurator = container.resolve(KEY_CONFIGURATOR_SERVICE)

        labels_file = labels_path or project_root / "translation" / "labels.tsv"
        metadata_service = UIMetadataService(configurator, labels_file)
        ui_repository = UIEventRepository(ui_db_path or str(project_root / "ui_events.db"))
        return cls(
            auth_service=auth_service,
            user_service=user_service,
            user_repository=user_repository,
            audit_service=audit_service,
            metadata_service=metadata_service,
            ui_repository=ui_repository,
        )

    def register_user(self, dto: UIRegisterDTO):
        """Register a new user via user management service."""
        try:
            UIPolicy.validate_registration(dto.username, dto.password, dto.email)
        except UIValidationError:
            raise
        role_key = (dto.role or "USER").upper()
        if role_key not in SystemRole.__members__:
            raise UIValidationError(f"Unbekannte Rolle: {dto.role}")
        role = SystemRole[role_key]
        created = self._user_service.create_user(
            CreateUserDTO(
                username=dto.username,
                password=dto.password,
                email=dto.email,
                role=role,
            ),
            actor_id=self._admin_id,
        )
        self._audit_service.log(
            user_id=self._admin_id,
            action="UI_REGISTER",
            feature="UI",
            log_level=LogLevel.INFO,
            severity=AuditSeverity.INFO,
            details={"username": created.username},
        )
        self._ui_repository.create_event(
            CreateUIEventDTO(
                username=created.username,
                action=UIAction.REGISTER.value,
                details={"role": created.role.value},
            )
        )
        return created

    def login(self, dto: UILoginDTO) -> AuthenticationResultDTO:
        """Authenticate a user and update UI context."""
        UIPolicy.validate_login(dto.username, dto.password)
        result = self._auth_service.login(
            LoginRequestDTO(username=dto.username, password=dto.password)
        )
        if not result.success or result.session is None:
            raise UIAuthenticationError(result.error_message or "Login fehlgeschlagen")

        self._context.session_id = result.session.session_id
        self._context.user_id = result.session.user_id
        self._context.username = result.session.username
        self._user_service.update_last_login(result.session.user_id)
        self._audit_service.log(
            user_id=result.session.user_id,
            action="UI_LOGIN",
            feature="UI",
            log_level=LogLevel.INFO,
            severity=AuditSeverity.INFO,
            details={"username": result.session.username},
        )
        self._ui_repository.create_event(
            CreateUIEventDTO(
                username=result.session.username,
                action=UIAction.LOGIN.value,
                details={"session_id": result.session.session_id},
            )
        )
        return result

    def logout(self) -> None:
        """Logout the current user."""
        if not self._context.session_id:
            return
        session_id = self._context.session_id
        username = self._context.username or "unknown"
        self._auth_service.logout(session_id)
        self._ui_repository.create_event(
            CreateUIEventDTO(
                username=username,
                action=UIAction.LOGOUT.value,
                details={"session_id": session_id},
            )
        )
        self._context = UIContext()

    def get_audit_logs(self, limit: int = 50) -> List[AuditLogDTO]:
        """Fetch audit logs."""
        return self._audit_service.get_logs(AuditLogFilterDTO(limit=limit))

    def get_ui_events(self, limit: int = 50) -> List[UIEventDTO]:
        """Fetch UI event logs."""
        return self._ui_repository.list_events(limit=limit)

    def load_meta_json(self) -> str:
        """Load formatted meta.json information."""
        return self._metadata_service.load_meta_json()

    def load_labels_tsv(self) -> str:
        """Load labels.tsv content."""
        return self._metadata_service.load_labels_tsv()

    def _ensure_admin_user(self) -> int:
        admin = self._user_repository.get_by_username("admin")
        if admin:
            return admin.id

        password_hash = bcrypt.hashpw("admin".encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        admin = self._user_repository.create(
            "admin",
            password_hash,
            SystemRole.ADMIN,
            "admin@example.com",
        )
        return admin.id
