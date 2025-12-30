"""QMToolV6 Test GUI.

Provides a simple Tkinter-based GUI to execute and verify key use cases
across the project.
"""
from __future__ import annotations

import json
import tempfile
import time
import traceback
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, List, Tuple

import tkinter as tk
from tkinter import ttk
from tkinter import scrolledtext

from core.container import Container
from core.container.exceptions import ServiceNotFoundError
from core.environment import load_config
from core.loader import Loader
from core.loader.exceptions import AuditSinkNotAvailableError
from core.loader.loader import KEY_DATABASE_SERVICE, parse_database_path


@dataclass
class UseCase:
    """Represents a testable use case for the GUI."""

    case_id: str
    title: str
    goal: str
    steps: str
    expected: str
    components: str
    runner: Callable[[], Tuple[bool, str]]


class UseCaseRunner:
    """Executes use cases and returns results."""

    def __init__(self, project_root: Path) -> None:
        self._project_root = project_root

    def loader_boot_happy_path(self) -> Tuple[bool, str]:
        loader = Loader(config_path=str(self._project_root / "config.ini"))
        boot_log = loader.boot()
        container = loader.get_container()
        has_database = container.is_registered(KEY_DATABASE_SERVICE)
        return bool(boot_log) and has_database, (
            f"Booted features: {boot_log}\n"
            f"Database service registered: {has_database}"
        )

    def loader_audit_missing(self) -> Tuple[bool, str]:
        loader = Loader(
            config_path=str(self._project_root / "config.ini"),
            skip_features=["audittrail"],
        )
        try:
            loader.boot()
        except AuditSinkNotAvailableError as exc:
            return True, f"Caught expected AuditSinkNotAvailableError: {exc}"
        return False, "Expected AuditSinkNotAvailableError, but boot succeeded"

    def loader_skip_features(self) -> Tuple[bool, str]:
        loader = Loader(
            config_path=str(self._project_root / "config.ini"),
            skip_features=["licensing"],
        )
        boot_log = loader.boot()
        skipped = "licensing" not in boot_log
        return skipped, f"Booted features: {boot_log}"

    def container_singleton_factory(self) -> Tuple[bool, str]:
        container = Container()
        container.add_singleton("x", lambda: {})
        container.add_factory("y", lambda: {})
        first_x = container.resolve("x")
        second_x = container.resolve("x")
        first_y = container.resolve("y")
        second_y = container.resolve("y")
        singleton_ok = first_x is second_x
        factory_ok = first_y is not second_y
        return singleton_ok and factory_ok, (
            f"Singleton same instance: {singleton_ok}\n"
            f"Factory returns new instance: {factory_ok}"
        )

    def container_service_not_found(self) -> Tuple[bool, str]:
        container = Container()
        try:
            container.resolve("nonexistent")
        except ServiceNotFoundError as exc:
            return True, f"Caught expected ServiceNotFoundError: {exc}"
        return False, "Expected ServiceNotFoundError, but resolve succeeded"

    def appenv_load_config_defaults(self) -> Tuple[bool, str]:
        missing_path = self._project_root / "does_not_exist.ini"
        env = load_config(str(missing_path), self._project_root)
        default_db = env.database_url == "sqlite:///qmtool.db"
        default_root = env.features_root == self._project_root
        return default_db and default_root, (
            f"database_url: {env.database_url}\n"
            f"features_root: {env.features_root}"
        )

    def appenv_parse_database_path(self) -> Tuple[bool, str]:
        file_path = parse_database_path("sqlite:///qm.db")
        memory_path = parse_database_path("sqlite:///:memory:")
        success = file_path == "qm.db" and memory_path == ":memory:"
        return success, f"file: {file_path} | memory: {memory_path}"

    def database_uow_create_entity(self) -> Tuple[bool, str]:
        from database.example_usage import ExampleService
        from database.logic.services.database_service import DatabaseService

        db_service = DatabaseService("sqlite:///:memory:")
        db_service.ensure_schema()
        service = ExampleService(db_service)
        created = service.create_example("sample", "value")
        retrieved = service.get_example(created["id"])
        success = retrieved is not None and retrieved["id"] == created["id"]
        return success, f"Created: {created}\nRetrieved: {retrieved}"

    def database_read_only_session(self) -> Tuple[bool, str]:
        from database.example_usage import ExampleService
        from database.logic.services.database_service import DatabaseService

        db_service = DatabaseService("sqlite:///:memory:")
        db_service.ensure_schema()
        service = ExampleService(db_service)
        created = service.create_example("readonly", "initial")
        retrieved = service.get_example(created["id"])
        success = retrieved is not None and retrieved["id"] == created["id"]
        return success, f"Retrieved via get_session: {retrieved}"

    def repository_crud(self) -> Tuple[bool, str]:
        from database.example_usage import ExampleEntity, ExampleRepository
        from database.logic.services.database_service import DatabaseService

        db_service = DatabaseService("sqlite:///:memory:")
        db_service.ensure_schema()

        with db_service.unit_of_work() as uow:
            session = uow.get_session()
            repo = ExampleRepository(session)
            created = repo.create(ExampleEntity(name="crud", value="one"))
            created_id = created.id

        session = db_service.get_session()
        repo = ExampleRepository(session)
        fetched = repo.get_by_id(created_id)
        fetched.value = "two"
        repo.update(fetched)
        updated = repo.get_by_id(created_id)
        repo.delete(updated)
        deleted = repo.get_by_id(created_id)

        success = fetched is not None and updated.value == "two" and deleted is None
        return success, (
            f"Created ID: {created_id}\n"
            f"Updated value: {updated.value}\n"
            f"Deleted present: {deleted is not None}"
        )

    def user_management_create_and_read(self) -> Tuple[bool, str]:
        from user_management.dto.user_dto import CreateUserDTO
        from user_management.enum.user_enum import SystemRole
        from user_management.repository.user_repository import UserRepository
        from user_management.services.user_management_service import UserManagementService

        repo = UserRepository()
        admin = repo.create("admin", "hash", SystemRole.ADMIN, "admin@example.com")
        service = UserManagementService(repo)
        created = service.create_user(
            CreateUserDTO(
                username="alice",
                password="StrongPass1!",
                email="alice@example.com",
                role=SystemRole.USER,
            ),
            actor_id=admin.id,
        )
        fetched = service.get_user_by_id(created.id, actor_id=admin.id)
        success = fetched.username == "alice"
        return success, f"Created: {created}\nFetched: {fetched}"

    def authenticator_login_creates_session(self) -> Tuple[bool, str]:
        import bcrypt
        from authenticator.dto.auth_dto import LoginRequestDTO
        from authenticator.services.authenticator_service import AuthenticatorService
        from shared.database.base import Base, create_session_factory
        from user_management.enum.user_enum import SystemRole
        from user_management.repository.user_repository import UserRepository

        session_factory = create_session_factory("sqlite:///:memory:")
        session = session_factory()
        Base.metadata.create_all(bind=session.get_bind())

        repo = UserRepository()
        password_hash = bcrypt.hashpw(b"Password1!", bcrypt.gensalt()).decode("utf-8")
        user = repo.create("tester", password_hash, SystemRole.USER, "tester@example.com")

        service = AuthenticatorService(session, repo)
        result = service.login(LoginRequestDTO(username="tester", password="Password1!"))
        session_created = result.success and result.session is not None
        return session_created, f"Authentication result: {result}"

    def authenticator_invalid_credentials(self) -> Tuple[bool, str]:
        import bcrypt
        from authenticator.dto.auth_dto import LoginRequestDTO
        from authenticator.services.authenticator_service import AuthenticatorService
        from shared.database.base import Base, create_session_factory
        from user_management.enum.user_enum import SystemRole
        from user_management.repository.user_repository import UserRepository

        session_factory = create_session_factory("sqlite:///:memory:")
        session = session_factory()
        Base.metadata.create_all(bind=session.get_bind())

        repo = UserRepository()
        password_hash = bcrypt.hashpw(b"Password1!", bcrypt.gensalt()).decode("utf-8")
        repo.create("tester", password_hash, SystemRole.USER, "tester@example.com")

        service = AuthenticatorService(session, repo)
        result = service.login(LoginRequestDTO(username="tester", password="WrongPass1!"))
        success = not result.success
        return success, f"Authentication result: {result}"

    def audittrail_create_log(self) -> Tuple[bool, str]:
        from audittrail.dto.audit_dto import AuditLogFilterDTO
        from audittrail.enum.audit_enum import AuditSeverity, LogLevel
        from audittrail.repository.audit_repository import AuditRepository
        from audittrail.services.audit_service import AuditService
        from audittrail.services.policy.audit_policy import AuditPolicy
        from configurator.repository.config_repository import ConfigRepository
        from configurator.repository.feature_repository import FeatureRepository
        from configurator.services.configurator_service import ConfiguratorService

        repo = AuditRepository(":memory:")
        policy = AuditPolicy()
        configurator = ConfiguratorService(
            FeatureRepository(str(self._project_root)),
            ConfigRepository(str(self._project_root)),
        )
        service = AuditService(repo, policy, configurator)

        log_id = service.log(
            user_id=0,
            action="LOGIN",
            feature="authenticator",
            log_level=LogLevel.INFO,
            severity=AuditSeverity.INFO,
            details={"note": "audit log"},
        )
        logs = repo.find_by_filters(AuditLogFilterDTO(action="LOGIN"))
        success = any(log.id == log_id for log in logs)
        return success, f"Created log id: {log_id}\nLogs found: {len(logs)}"

    def authenticator_audit_integration(self) -> Tuple[bool, str]:
        import bcrypt
        from authenticator.dto.auth_dto import LoginRequestDTO
        from authenticator.services.authenticator_service import AuthenticatorService
        from audittrail.dto.audit_dto import AuditLogFilterDTO
        from audittrail.enum.audit_enum import AuditSeverity, LogLevel
        from audittrail.repository.audit_repository import AuditRepository
        from audittrail.services.audit_service import AuditService
        from audittrail.services.policy.audit_policy import AuditPolicy
        from configurator.repository.config_repository import ConfigRepository
        from configurator.repository.feature_repository import FeatureRepository
        from configurator.services.configurator_service import ConfiguratorService
        from shared.database.base import Base, create_session_factory
        from user_management.enum.user_enum import SystemRole
        from user_management.repository.user_repository import UserRepository

        session_factory = create_session_factory("sqlite:///:memory:")
        session = session_factory()
        Base.metadata.create_all(bind=session.get_bind())

        user_repo = UserRepository()
        password_hash = bcrypt.hashpw(b"Password1!", bcrypt.gensalt()).decode("utf-8")
        user_repo.create("audited", password_hash, SystemRole.USER, "audit@example.com")

        auth_service = AuthenticatorService(session, user_repo)

        audit_repo = AuditRepository(":memory:")
        audit_policy = AuditPolicy()
        configurator = ConfiguratorService(
            FeatureRepository(str(self._project_root)),
            ConfigRepository(str(self._project_root)),
        )
        audit_service = AuditService(audit_repo, audit_policy, configurator)

        result = auth_service.login(LoginRequestDTO(username="audited", password="Password1!"))

        logs = audit_repo.find_by_filters(AuditLogFilterDTO(action="LOGIN"))
        success = result.success and any(log.action == "LOGIN" for log in logs)
        return success, (
            f"Authentication result: {result}\n"
            f"Audit logs with LOGIN: {len(logs)}"
        )

    def audittrail_filter_export(self) -> Tuple[bool, str]:
        from audittrail.dto.audit_dto import AuditLogFilterDTO
        from audittrail.enum.audit_enum import AuditSeverity, LogLevel
        from audittrail.repository.audit_repository import AuditRepository
        from audittrail.services.audit_service import AuditService
        from audittrail.services.policy.audit_policy import AuditPolicy
        from configurator.repository.config_repository import ConfigRepository
        from configurator.repository.feature_repository import FeatureRepository
        from configurator.services.configurator_service import ConfiguratorService

        repo = AuditRepository(":memory:")
        policy = AuditPolicy()
        configurator = ConfiguratorService(
            FeatureRepository(str(self._project_root)),
            ConfigRepository(str(self._project_root)),
        )
        service = AuditService(repo, policy, configurator)

        service.log(
            user_id=0,
            action="LOGIN",
            feature="authenticator",
            log_level=LogLevel.INFO,
            severity=AuditSeverity.INFO,
            details={"note": "one"},
        )
        service.log(
            user_id=0,
            action="LOGOUT",
            feature="authenticator",
            log_level=LogLevel.INFO,
            severity=AuditSeverity.INFO,
            details={"note": "two"},
        )

        filtered = service.get_logs(AuditLogFilterDTO(action="LOGIN"))
        json_export = service.export_logs(AuditLogFilterDTO(action="LOGIN"), format="json")
        csv_export = service.export_logs(AuditLogFilterDTO(action="LOGIN"), format="csv")
        json_valid = bool(json.loads(json_export))
        csv_valid = "LOGIN" in csv_export
        success = len(filtered) == 1 and json_valid and csv_valid
        return success, (
            f"Filtered logs: {len(filtered)}\n"
            f"JSON length: {len(json_export)} | CSV length: {len(csv_export)}"
        )

    def audittrail_retention_cleanup(self) -> Tuple[bool, str]:
        from datetime import datetime, timedelta

        from audittrail.dto.audit_dto import AuditLogFilterDTO
        from audittrail.enum.audit_enum import AuditSeverity, LogLevel
        from audittrail.repository.audit_repository import AuditRepository
        from audittrail.services.audit_service import AuditService
        from audittrail.services.policy.audit_policy import AuditPolicy
        from configurator.repository.config_repository import ConfigRepository
        from configurator.repository.feature_repository import FeatureRepository
        from configurator.services.configurator_service import ConfiguratorService

        repo = AuditRepository(":memory:")
        policy = AuditPolicy()
        configurator = ConfiguratorService(
            FeatureRepository(str(self._project_root)),
            ConfigRepository(str(self._project_root)),
        )
        service = AuditService(repo, policy, configurator)

        old_log_id = service.log(
            user_id=0,
            action="LOGIN",
            feature="authenticator",
            log_level=LogLevel.INFO,
            severity=AuditSeverity.INFO,
            details={"note": "old"},
        )
        new_log_id = service.log(
            user_id=0,
            action="LOGIN",
            feature="authenticator",
            log_level=LogLevel.INFO,
            severity=AuditSeverity.INFO,
            details={"note": "new"},
        )

        old_timestamp = (datetime.now() - timedelta(days=400)).isoformat()
        repo._conn.execute(
            "UPDATE audit_logs SET timestamp = ? WHERE id = ?",
            (old_timestamp, old_log_id),
        )
        repo._conn.commit()

        deleted = service.delete_old_logs(retention_days=365)
        remaining_logs = repo.find_by_filters(AuditLogFilterDTO(action="LOGIN"))
        remaining_ids = {log.id for log in remaining_logs}
        success = deleted >= 1 and new_log_id in remaining_ids and old_log_id not in remaining_ids
        return success, (
            f"Deleted: {deleted}\n"
            f"Remaining IDs: {sorted(remaining_ids)}"
        )

    def feature_module_lifecycle(self) -> Tuple[bool, str]:
        from core.environment.app_env import AppEnv
        from core.loader.feature_module import FeatureModule

        class ExampleModule(FeatureModule):
            def __init__(self) -> None:
                self.started = False

            @property
            def feature_id(self) -> str:
                return "example"

            def register(self, container: Container, env: AppEnv) -> None:
                container.add_singleton("example.service", lambda: {"env": env})

            def start(self, container: Container) -> None:
                self.started = True

        env = AppEnv(project_root=self._project_root, features_root=self._project_root)
        container = Container()
        module = ExampleModule()
        module.register(container, env)
        module.start(container)

        registered = container.is_registered("example.service")
        started = module.started
        return registered and started, (
            f"Service registered: {registered}\n"
            f"Module started: {started}"
        )

    def legacy_db_access(self) -> Tuple[bool, str]:
        from sqlalchemy import text
        from database.logic.services.database_service import DatabaseService

        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            db_path = tmp.name

        db_service = DatabaseService(f"sqlite:///{db_path}")
        db_service.ensure_schema()
        connection = db_service.get_connection()
        connection.execute("CREATE TABLE IF NOT EXISTS legacy (id INTEGER PRIMARY KEY, name TEXT)")
        connection.execute("INSERT INTO legacy (name) VALUES (?)", ("legacy",))
        connection.commit()

        session = db_service.get_session()
        result = session.execute(text("SELECT name FROM legacy"))
        names = [row[0] for row in result.fetchall()]
        success = "legacy" in names
        return success, f"Legacy names via SQLAlchemy: {names}"

    def database_health_check(self) -> Tuple[bool, str]:
        from database.logic.services.database_service import DatabaseService
        from database.logic.services.healthcheck_service import HealthcheckService

        db_service = DatabaseService("sqlite:///:memory:")
        db_service.ensure_schema()
        health_service = HealthcheckService(db_service)
        result = health_service.check_health()
        return result.is_healthy, f"Health: {result}"


class TestGuiApp:
    """Tkinter GUI for running use case checks."""

    def __init__(self, root: tk.Tk, use_cases: List[UseCase]) -> None:
        self._root = root
        self._use_cases = use_cases
        self._case_lookup: Dict[str, UseCase] = {case.case_id: case for case in use_cases}
        self._status: Dict[str, str] = {}

        self._root.title("QMToolV6 Use Case GUI")
        self._root.geometry("1100x700")

        self._build_ui()

    def _build_ui(self) -> None:
        header = ttk.Label(
            self._root,
            text="QMToolV6 Use Case Test GUI",
            font=("Arial", 16, "bold"),
        )
        header.pack(pady=10)

        main_frame = ttk.Frame(self._root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        left_frame = ttk.Frame(main_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=False)

        right_frame = ttk.Frame(main_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self._tree = ttk.Treeview(left_frame, columns=("title", "status"), show="headings")
        self._tree.heading("title", text="Use Case")
        self._tree.heading("status", text="Status")
        self._tree.column("title", width=380, anchor=tk.W)
        self._tree.column("status", width=90, anchor=tk.CENTER)
        self._tree.pack(fill=tk.BOTH, expand=True)

        for case in self._use_cases:
            self._tree.insert(
                "",
                tk.END,
                iid=case.case_id,
                values=(case.title, ""),
            )

        self._tree.bind("<<TreeviewSelect>>", self._on_select)

        details_label = ttk.Label(right_frame, text="Details", font=("Arial", 12, "bold"))
        details_label.pack(anchor=tk.W)

        self._details_text = scrolledtext.ScrolledText(right_frame, height=12, wrap=tk.WORD)
        self._details_text.pack(fill=tk.BOTH, expand=False)
        self._details_text.configure(state=tk.DISABLED)

        log_label = ttk.Label(right_frame, text="Execution Log", font=("Arial", 12, "bold"))
        log_label.pack(anchor=tk.W, pady=(10, 0))

        self._log_text = scrolledtext.ScrolledText(right_frame, height=14, wrap=tk.WORD)
        self._log_text.pack(fill=tk.BOTH, expand=True)

        button_frame = ttk.Frame(self._root)
        button_frame.pack(fill=tk.X, padx=10, pady=10)

        run_selected = ttk.Button(button_frame, text="Run Selected", command=self._run_selected)
        run_selected.pack(side=tk.LEFT, padx=5)

        run_all = ttk.Button(button_frame, text="Run All", command=self._run_all)
        run_all.pack(side=tk.LEFT, padx=5)

        clear_log = ttk.Button(button_frame, text="Clear Log", command=self._clear_log)
        clear_log.pack(side=tk.RIGHT, padx=5)

        if self._use_cases:
            self._tree.selection_set(self._use_cases[0].case_id)
            self._update_details(self._use_cases[0])

    def _update_details(self, case: UseCase) -> None:
        details = (
            f"{case.title}\n\n"
            f"Ziel:\n{case.goal}\n\n"
            f"Schritte:\n{case.steps}\n\n"
            f"Erwartet:\n{case.expected}\n\n"
            f"Komponenten:\n{case.components}\n"
        )
        self._details_text.configure(state=tk.NORMAL)
        self._details_text.delete("1.0", tk.END)
        self._details_text.insert(tk.END, details)
        self._details_text.configure(state=tk.DISABLED)

    def _on_select(self, _event: tk.Event) -> None:
        selection = self._tree.selection()
        if not selection:
            return
        case_id = selection[0]
        case = self._case_lookup.get(case_id)
        if case:
            self._update_details(case)

    def _log(self, message: str) -> None:
        self._log_text.insert(tk.END, message + "\n")
        self._log_text.see(tk.END)

    def _run_case(self, case: UseCase) -> None:
        start = time.perf_counter()
        try:
            success, detail = case.runner()
        except Exception as exc:
            success = False
            detail = f"{type(exc).__name__}: {exc}\n{traceback.format_exc()}"
        duration = (time.perf_counter() - start) * 1000
        status = "PASS" if success else "FAIL"
        self._tree.set(case.case_id, "status", status)
        self._log(
            f"[{status}] {case.title} ({duration:.1f} ms)\n{detail}\n"
        )

    def _run_selected(self) -> None:
        selection = self._tree.selection()
        if not selection:
            return
        case = self._case_lookup.get(selection[0])
        if case:
            self._run_case(case)

    def _run_all(self) -> None:
        for case in self._use_cases:
            self._run_case(case)

    def _clear_log(self) -> None:
        self._log_text.delete("1.0", tk.END)


def build_use_cases(project_root: Path) -> List[UseCase]:
    runner = UseCaseRunner(project_root)
    return [
        UseCase(
            case_id="loader_boot",
            title="Loader: Booten der Anwendung (Happy Path)",
            goal="Loader bootet erfolgreich und registriert Features in DI-Container.",
            steps="Loader mit default config.ini starten (Loader.boot()).",
            expected="Liste der gebooteten Feature-IDs zurück, Container enthält erwartete Keys.",
            components="core/loader/loader.py, core/container/container.py, core/environment/config_loader.py",
            runner=runner.loader_boot_happy_path,
        ),
        UseCase(
            case_id="loader_audit_missing",
            title="Loader: Audit-Sink erzwingt Boot-Failure",
            goal="Loader wirft AuditSinkNotAvailableError, wenn Audit nicht registriert ist.",
            steps="Loader so konfigurieren, dass audittrail fehlt; boot() aufrufen.",
            expected="AuditSinkNotAvailableError (Boot abgebrochen).",
            components="core/loader/loader.py, core/loader/exceptions.py",
            runner=runner.loader_audit_missing,
        ),
        UseCase(
            case_id="loader_skip_features",
            title="Loader: skip_features fürs Testen",
            goal="Loader kann einzelne Features überspringen.",
            steps="Loader(skip_features=[\"licensing\"]).boot()",
            expected="Gebootete Feature-Liste enthält nicht die übersprungenen Features.",
            components="core/loader/loader.py",
            runner=runner.loader_skip_features,
        ),
        UseCase(
            case_id="container_singleton_factory",
            title="Container: Singleton vs Factory Verhalten",
            goal="DI-Container erzeugt Singleton-Instanz nur einmal, Factory immer neu.",
            steps="add_singleton/add_factory; resolve mehrfach.",
            expected="Singleton liefert identische, Factory unterschiedliche Objekte.",
            components="core/container/container.py",
            runner=runner.container_singleton_factory,
        ),
        UseCase(
            case_id="container_service_not_found",
            title="Container: ServiceNotFound-Fehler testen",
            goal="Anfrage eines nicht-registrierten Keys wirft ServiceNotFoundError.",
            steps="container.resolve(\"nonexistent\") aufrufen.",
            expected="ServiceNotFoundError.",
            components="core/container/exceptions.py, core/container/container.py",
            runner=runner.container_service_not_found,
        ),
        UseCase(
            case_id="appenv_defaults",
            title="AppEnv: load_config mit fehlender config.ini (Defaults)",
            goal="load_config verwendet Defaults, wenn config.ini fehlt.",
            steps="load_config(config_path auf nicht-existierende Datei)",
            expected="AppEnv mit default database_url und feature_root = project_root.",
            components="core/environment/config_loader.py, core/environment/app_env.py",
            runner=runner.appenv_load_config_defaults,
        ),
        UseCase(
            case_id="appenv_parse_db",
            title="AppEnv: parse_database_path - sqlite file vs memory",
            goal="parse_database_path wandelt URL korrekt in Pfad um.",
            steps="parse_database_path(\"sqlite:///qm.db\"), parse_database_path(\"sqlite:///:memory:\")",
            expected="\"qm.db\" bzw. \" :memory: \".",
            components="core/loader/loader.py (parse_database_path)",
            runner=runner.appenv_parse_database_path,
        ),
        UseCase(
            case_id="database_uow",
            title="Database: Unit-of-Work create entity (Beispiel)",
            goal="Beispielservice legt Datensatz an via Unit-of-Work.",
            steps="ExampleService.create_example(...) mit In-Memory DB.",
            expected="Rückgabe mit id; get_example findet Datensatz.",
            components="database/example_usage.py, database/README.md",
            runner=runner.database_uow_create_entity,
        ),
        UseCase(
            case_id="database_readonly",
            title="Database: Read-Only Session get_session funktioniert",
            goal="get_session liefert Session für SELECT-Operationen ohne UoW.",
            steps="ExampleService.get_example(...) nach create ausführen.",
            expected="Entität wird gelesen ohne Transaktionsprobleme.",
            components="database/example_usage.py, database.logic.services.database_service",
            runner=runner.database_read_only_session,
        ),
        UseCase(
            case_id="repository_crud",
            title="Repository: BaseRepository CRUD Grundfunktion",
            goal="BaseRepository ermöglicht create/get_by_id/update/delete.",
            steps="ExampleRepository verwenden, CRUD-Methoden aufrufen.",
            expected="Entitäten werden persistent und Änderungen sichtbar.",
            components="database/logic/repository/base_repository.py, database/example_usage.py",
            runner=runner.repository_crud,
        ),
        UseCase(
            case_id="user_management",
            title="User Management: Benutzer anlegen und Lesen",
            goal="UserManagementService legt neuen Benutzer an und kann ihn zurückgeben.",
            steps="CreateUserDTO verwenden; anschließend get_user_by_id.",
            expected="Neuer Benutzer in DB vorhanden.",
            components="user_management (README beschreibt DTOs und Repo-Pattern)",
            runner=runner.user_management_create_and_read,
        ),
        UseCase(
            case_id="auth_login_session",
            title="Authenticator: Login erzeugt Session in SessionRepository",
            goal="Erfolgreicher Login erzeugt Session-Eintrag.",
            steps="AuthenticatorService.login(username,password) aufrufen.",
            expected="Session-Entity gespeichert; Rückgabe SessionDTO.",
            components="authenticator/services/authenticator_service.py, authenticator/repository/session_repository.py",
            runner=runner.authenticator_login_creates_session,
        ),
        UseCase(
            case_id="auth_invalid",
            title="Authenticator: Ungültige Credentials",
            goal="Falsches Passwort wird erkannt.",
            steps="login mit falschem Passwort.",
            expected="InvalidCredentialsException bzw. result.success=False.",
            components="authenticator/exceptions.py, authenticator/services/authenticator_service.py",
            runner=runner.authenticator_invalid_credentials,
        ),
        UseCase(
            case_id="audit_create_log",
            title="AuditTrail: Erzeuge Audit-Log bei Aktion",
            goal="AuditService nimmt Logeintrag an und persistiert ihn.",
            steps="audit_service.log(action=\"LOGIN\", actor=...)",
            expected="AuditRepository enthält neuen Log-Eintrag.",
            components="audittrail/services/audit_service.py, audittrail/repository/audit_repository.py",
            runner=runner.audittrail_create_log,
        ),
        UseCase(
            case_id="auth_audit_integration",
            title="Integration Authenticator ↔ AuditTrail",
            goal="Login schreibt Audit-Event (Integrationstest).",
            steps="login durchführen, danach AuditRepository nach LOGIN filtern.",
            expected="Audit-Eintrag mit action=LOGIN, actor=username.",
            components="authenticator (service), audittrail (service & repo), core/container",
            runner=runner.authenticator_audit_integration,
        ),
        UseCase(
            case_id="audit_filter_export",
            title="AuditTrail: Filter & Export (JSON/CSV)",
            goal="Audit-Repository gibt Filterergebnis zurück und kann exportieren.",
            steps="Logs erzeugen; filter_logs; export(format=\"csv\").",
            expected="Gefilterte Liste und gültige CSV/JSON-Ausgabe.",
            components="audittrail/dto/audit_dto.py, audittrail/services, audittrail/repository",
            runner=runner.audittrail_filter_export,
        ),
        UseCase(
            case_id="audit_retention",
            title="Audit Retention-Cleanup Policy ausführen",
            goal="Retention-Policy löscht Logs älter als global_retention_days.",
            steps="Alten Log erzeugen; retention/cleanup ausführen.",
            expected="Alter Log gelöscht; neuere bleiben.",
            components="audittrail/services/policy/audit_policy.py, core/environment.AppEnv",
            runner=runner.audittrail_retention_cleanup,
        ),
        UseCase(
            case_id="feature_module",
            title="FeatureModule: register() und start() Lifecycle testen",
            goal="FeatureModule registriert Services und start() führt Startup-Aufgaben aus.",
            steps="Minimal FeatureModule implementieren; Container verwenden.",
            expected="Service im Container vorhanden; start() ohne Fehler.",
            components="core/loader/feature_module.py, core/container/container.py",
            runner=runner.feature_module_lifecycle,
        ),
        UseCase(
            case_id="legacy_db",
            title="Legacy DB Access: sqlite3.Connection benutzen",
            goal="Legacy-Zugriff auf DB (raw SQL) funktioniert parallel zur ORM-Schicht.",
            steps="sqlite3.connect verwenden; Reads/Writes testen.",
            expected="Reads/Writes konsistent; keine Sperrprobleme.",
            components="database/README.md, core/environment/app_env.py",
            runner=runner.legacy_db_access,
        ),
        UseCase(
            case_id="health_check",
            title="Health-Check: DatabaseService connectivity check",
            goal="DatabaseService meldet Verbindungsstatus (Health Check).",
            steps="health_check() bzw. SELECT 1 ausführen.",
            expected="Health OK bei erreichbarer DB.",
            components="database.logic.services.database_service, core/loader.parse_database_path",
            runner=runner.database_health_check,
        ),
    ]


def main() -> None:
    project_root = Path(__file__).resolve().parent
    root = tk.Tk()
    app = TestGuiApp(root, build_use_cases(project_root))
    root.mainloop()


if __name__ == "__main__":
    main()
