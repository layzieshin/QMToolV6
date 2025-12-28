"""
Translation Test Fixtures
==========================

Shared pytest fixtures for Translation feature tests.
"""

import pytest
from pathlib import Path
from typing import Dict
from unittest.mock import Mock

from translation.repository.translation_repository import InMemoryTranslationRepository
from translation.services.feature_discovery_service import FeatureDiscoveryService
from translation.services.translation_service import TranslationService
from translation.services.policy.translation_policy import TranslationPolicy
from translation.dto.translation_dto import TranslationSetDTO
from translation.enum.translation_enum import SupportedLanguage

# Mock user management dependencies
from user_management.dto.user_dto import UserDTO
from user_management.enum.user_enum import SystemRole, UserStatus


@pytest.fixture
def translation_repository():
    """Fixture providing fresh in-memory translation repository."""
    return InMemoryTranslationRepository()


@pytest.fixture
def sample_translations() -> Dict[str, TranslationSetDTO]:
    """Fixture providing sample translation data."""
    return {
        "core. save": TranslationSetDTO(
            label="core.save",
            feature="core",
            translations={
                SupportedLanguage.DE: "Speichern",
                SupportedLanguage.EN: "Save"
            }
        ),
        "core.cancel": TranslationSetDTO(
            label="core.cancel",
            feature="core",
            translations={
                SupportedLanguage.DE: "Abbrechen",
                SupportedLanguage.EN: "Cancel"
            }
        ),
        "core.missing": TranslationSetDTO(
            label="core.missing",
            feature="core",
            translations={
                SupportedLanguage.DE: "Deutsch",
                SupportedLanguage.EN: ""  # Missing EN translation
            }
        ),
    }


@pytest.fixture
def populated_repository(translation_repository, sample_translations):
    """Fixture providing repository populated with sample data."""
    for trans_set in sample_translations.values():
        translation_repository.create_translation_set(trans_set)
    return translation_repository


@pytest.fixture
def mock_user_service():
    """Fixture providing mocked UserManagementService."""
    mock_service = Mock()

    # Setup mock users
    admin_user = UserDTO(
        id=1,
        username="admin",
        full_name="Admin User",
        email="admin@test.com",
        role=SystemRole.ADMIN,
        status=UserStatus.ACTIVE
    )

    qmb_user = UserDTO(
        id=2,
        username="qmb",
        full_name="QMB User",
        email="qmb@test.com",
        role=SystemRole.QMB,
        status=UserStatus.ACTIVE
    )

    regular_user = UserDTO(
        id=3,
        username="user",
        full_name="Regular User",
        email="user@test.com",
        role=SystemRole.USER,
        status=UserStatus.ACTIVE
    )

    # Configure mock behavior
    def get_user_by_id(user_id: int):
        users = {1: admin_user, 2: qmb_user, 3: regular_user}
        return users.get(user_id)

    mock_service.get_user_by_id.side_effect = get_user_by_id

    return mock_service


@pytest.fixture
def admin_user():
    """Fixture providing admin UserDTO."""
    return UserDTO(
        id=1,
        username="admin",
        full_name="Admin User",
        email="admin@test.com",
        role=SystemRole.ADMIN,
        status=UserStatus.ACTIVE
    )


@pytest.fixture
def qmb_user():
    """Fixture providing QMB UserDTO."""
    return UserDTO(
        id=2,
        username="qmb",
        full_name="QMB User",
        email="qmb@test.com",
        role=SystemRole.QMB,
        status=UserStatus.ACTIVE
    )


@pytest.fixture
def regular_user():
    """Fixture providing regular UserDTO."""
    return UserDTO(
        id=3,
        username="user",
        full_name="Regular User",
        email="user@test. com",
        role=SystemRole.USER,
        status=UserStatus.ACTIVE
    )


@pytest.fixture
def translation_policy(mock_user_service):
    """Fixture providing translation policy with mocked user service."""
    return TranslationPolicy(mock_user_service)


@pytest.fixture
def mock_audit_service():
    """Fixture providing mocked AuditService."""
    return Mock()


@pytest.fixture
def feature_discovery_service(tmp_path):
    """Fixture providing feature discovery service with temp directory."""
    return FeatureDiscoveryService(tmp_path)


@pytest.fixture
def translation_service(
        populated_repository,
        translation_policy,
        mock_audit_service,
        feature_discovery_service
):
    """Fixture providing fully configured TranslationService."""
    return TranslationService(
        repository=populated_repository,
        policy=translation_policy,
        audit_service=mock_audit_service,
        discovery_service=feature_discovery_service
    )


@pytest.fixture
def temp_tsv_file(tmp_path):
    """Fixture providing temporary TSV file path."""
    tsv_path = tmp_path / "test_labels.tsv"
    content = """label\tde\ten
test. key1\tWert 1\tValue 1
test.key2\tWert 2\tValue 2
test.missing\tVorhanden\t
"""
    tsv_path.write_text(content, encoding="utf-8")
    return tsv_path


@pytest.fixture
def mock_feature_structure(tmp_path):
    """Fixture creating mock feature directory structure."""
    # Create authenticator feature
    auth_dir = tmp_path / "authenticator"
    auth_dir.mkdir()
    (auth_dir / "meta.json").write_text('{"feature_name": "authenticator"}')
    (auth_dir / "labels.tsv").write_text("label\tde\ten\nauth.login\tAnmelden\tLogin\n")

    # Create user_management feature
    user_dir = tmp_path / "user_management"
    user_dir.mkdir()
    (user_dir / "meta.json").write_text('{"feature_name": "user_management"}')
    (user_dir / "labels.tsv").write_text("label\tde\ten\nuser.create\tErstellen\tCreate\n")

    # Create feature without labels. tsv (should be skipped)
    incomplete_dir = tmp_path / "incomplete"
    incomplete_dir.mkdir()
    (incomplete_dir / "meta.json").write_text('{"feature_name": "incomplete"}')

    return tmp_path