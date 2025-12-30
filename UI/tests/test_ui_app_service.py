"""Tests for UIAppService."""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from authenticator.services.authenticator_service import AuthenticatorService
from shared.database.base import Base
from user_management.repository.user_repository import UserRepository
from user_management.services.user_management_service import UserManagementService

from UI.dto.ui_dto import UIRegisterDTO, UILoginDTO
from UI.enum.ui_enum import UIAction
from UI.repository.ui_repository import UIEventRepository
from UI.services.ui_app_service import UIAppService


class StubAuditService:
    def __init__(self):
        self.logged = []

    def log(self, **kwargs):
        self.logged.append(kwargs)
        return 1

    def get_logs(self, _filters):
        return []


class StubMetadataService:
    def load_meta_json(self):
        return "{}"

    def load_labels_tsv(self):
        return "label\tde\ten"


def test_ui_app_service_register_and_login(tmp_path):
    user_repo = UserRepository()
    user_service = UserManagementService(user_repo)

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    auth_service = AuthenticatorService(session, user_repo)

    ui_repo = UIEventRepository(str(tmp_path / "ui.db"))

    service = UIAppService(
        auth_service=auth_service,
        user_service=user_service,
        user_repository=user_repo,
        audit_service=StubAuditService(),
        metadata_service=StubMetadataService(),
        ui_repository=ui_repo,
    )

    assert user_repo.get_by_username("admin") is not None

    service.register_user(
        UIRegisterDTO(
            username="alice",
            password="StrongPass1!",
            email="alice@example.com",
            role="USER",
        )
    )

    result = service.login(UILoginDTO(username="alice", password="StrongPass1!"))
    assert result.success is True

    events = service.get_ui_events()
    assert any(event.action == UIAction.LOGIN.value for event in events)
