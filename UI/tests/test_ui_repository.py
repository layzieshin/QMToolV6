"""Tests for UIEventRepository."""
from UI.dto.ui_dto import CreateUIEventDTO
from UI.repository.ui_repository import UIEventRepository


def test_ui_repository_creates_and_lists_events(tmp_path):
    db_path = tmp_path / "ui_events.db"
    repo = UIEventRepository(str(db_path))

    created = repo.create_event(
        CreateUIEventDTO(username="alice", action="login", details={"ip": "127.0.0.1"})
    )
    events = repo.list_events()

    assert created.id is not None
    assert len(events) == 1
    assert events[0].username == "alice"
    assert events[0].details == {"ip": "127.0.0.1"}
