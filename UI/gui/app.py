"""Tkinter GUI for UI feature integration tests."""
from __future__ import annotations

from pathlib import Path
import tkinter as tk
from tkinter import ttk, scrolledtext

from user_management.enum.user_enum import SystemRole

from UI.dto.ui_dto import UILoginDTO, UIRegisterDTO
from UI.exceptions.ui_exceptions import UIAuthenticationError, UIValidationError, UIDataLoadError
from UI.services.ui_app_service import UIAppService


class UIApp:
    """Tkinter GUI to exercise core integration."""

    def __init__(self, root: tk.Tk) -> None:
        self._root = root
        self._root.title("QMToolV6 UI Integration")
        self._root.geometry("980x720")

        project_root = Path(__file__).resolve().parents[2]
        self._service = UIAppService.from_loader(
            project_root=project_root,
            config_path=str(project_root / "config.ini"),
        )

        self._notebook = ttk.Notebook(self._root)
        self._notebook.pack(fill=tk.BOTH, expand=True)

        self._build_login_tab()
        self._build_register_tab()
        self._build_logs_tab()
        self._build_metadata_tab()

    def _build_login_tab(self) -> None:
        frame = ttk.Frame(self._notebook)
        self._notebook.add(frame, text="Login")

        ttk.Label(frame, text="Benutzername").grid(row=0, column=0, sticky="w", padx=8, pady=8)
        self._login_username = ttk.Entry(frame, width=30)
        self._login_username.grid(row=0, column=1, padx=8, pady=8)

        ttk.Label(frame, text="Passwort").grid(row=1, column=0, sticky="w", padx=8, pady=8)
        self._login_password = ttk.Entry(frame, width=30, show="*")
        self._login_password.grid(row=1, column=1, padx=8, pady=8)

        self._login_status = ttk.Label(frame, text="")
        self._login_status.grid(row=3, column=0, columnspan=2, sticky="w", padx=8, pady=8)

        ttk.Button(frame, text="Anmelden", command=self._handle_login).grid(
            row=2, column=0, columnspan=2, pady=10
        )

    def _build_register_tab(self) -> None:
        frame = ttk.Frame(self._notebook)
        self._notebook.add(frame, text="Neuer Benutzer")

        ttk.Label(frame, text="Benutzername").grid(row=0, column=0, sticky="w", padx=8, pady=8)
        self._register_username = ttk.Entry(frame, width=30)
        self._register_username.grid(row=0, column=1, padx=8, pady=8)

        ttk.Label(frame, text="Passwort").grid(row=1, column=0, sticky="w", padx=8, pady=8)
        self._register_password = ttk.Entry(frame, width=30, show="*")
        self._register_password.grid(row=1, column=1, padx=8, pady=8)

        ttk.Label(frame, text="E-Mail").grid(row=2, column=0, sticky="w", padx=8, pady=8)
        self._register_email = ttk.Entry(frame, width=30)
        self._register_email.grid(row=2, column=1, padx=8, pady=8)

        ttk.Label(frame, text="Rolle").grid(row=3, column=0, sticky="w", padx=8, pady=8)
        self._register_role = ttk.Combobox(
            frame,
            values=[role.value for role in SystemRole],
            state="readonly",
        )
        self._register_role.set(SystemRole.USER.value)
        self._register_role.grid(row=3, column=1, padx=8, pady=8)

        self._register_status = ttk.Label(frame, text="")
        self._register_status.grid(row=5, column=0, columnspan=2, sticky="w", padx=8, pady=8)

        ttk.Button(frame, text="Benutzer anlegen", command=self._handle_register).grid(
            row=4, column=0, columnspan=2, pady=10
        )

    def _build_logs_tab(self) -> None:
        frame = ttk.Frame(self._notebook)
        self._notebook.add(frame, text="Logs")

        self._logs_notebook = ttk.Notebook(frame)
        self._logs_notebook.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        audit_frame = ttk.Frame(self._logs_notebook)
        ui_frame = ttk.Frame(self._logs_notebook)

        self._logs_notebook.add(audit_frame, text="Audit Logs")
        self._logs_notebook.add(ui_frame, text="UI Events")

        self._audit_text = scrolledtext.ScrolledText(audit_frame, height=25)
        self._audit_text.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)
        ttk.Button(audit_frame, text="Aktualisieren", command=self._refresh_audit_logs).pack(pady=4)

        self._ui_text = scrolledtext.ScrolledText(ui_frame, height=25)
        self._ui_text.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)
        ttk.Button(ui_frame, text="Aktualisieren", command=self._refresh_ui_events).pack(pady=4)

    def _build_metadata_tab(self) -> None:
        frame = ttk.Frame(self._notebook)
        self._notebook.add(frame, text="Meta/Labels")

        self._meta_notebook = ttk.Notebook(frame)
        self._meta_notebook.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        meta_frame = ttk.Frame(self._meta_notebook)
        labels_frame = ttk.Frame(self._meta_notebook)

        self._meta_notebook.add(meta_frame, text="meta.json")
        self._meta_notebook.add(labels_frame, text="labels.tsv")

        self._meta_text = scrolledtext.ScrolledText(meta_frame, height=25)
        self._meta_text.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)

        self._labels_text = scrolledtext.ScrolledText(labels_frame, height=25)
        self._labels_text.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)

        self._meta_notebook.bind("<<NotebookTabChanged>>", self._handle_meta_tab_change)

    def _handle_login(self) -> None:
        dto = UILoginDTO(
            username=self._login_username.get().strip(),
            password=self._login_password.get().strip(),
        )
        try:
            result = self._service.login(dto)
            self._login_status.configure(text=f"Login erfolgreich: {result.session.username}")
        except (UIAuthenticationError, UIValidationError) as exc:
            self._login_status.configure(text=str(exc))

    def _handle_register(self) -> None:
        dto = UIRegisterDTO(
            username=self._register_username.get().strip(),
            password=self._register_password.get().strip(),
            email=self._register_email.get().strip() or None,
            role=self._register_role.get(),
        )
        try:
            user = self._service.register_user(dto)
            self._register_status.configure(text=f"Benutzer erstellt: {user.username}")
        except UIValidationError as exc:
            self._register_status.configure(text=str(exc))
        except Exception as exc:
            self._register_status.configure(text=f"Fehler: {exc}")

    def _refresh_audit_logs(self) -> None:
        logs = self._service.get_audit_logs()
        lines = [
            f"{log.timestamp} | {log.username} | {log.feature} | {log.action} | {log.log_level}"
            for log in logs
        ]
        self._audit_text.delete("1.0", tk.END)
        self._audit_text.insert(tk.END, "\n".join(lines))

    def _refresh_ui_events(self) -> None:
        events = self._service.get_ui_events()
        lines = [
            f"{event.timestamp} | {event.username} | {event.action} | {event.details}"
            for event in events
        ]
        self._ui_text.delete("1.0", tk.END)
        self._ui_text.insert(tk.END, "\n".join(lines))

    def _handle_meta_tab_change(self, _event: tk.Event) -> None:
        current = self._meta_notebook.tab(self._meta_notebook.select(), "text")
        if current == "meta.json":
            try:
                self._meta_text.delete("1.0", tk.END)
                self._meta_text.insert(tk.END, self._service.load_meta_json())
            except UIDataLoadError as exc:
                self._meta_text.delete("1.0", tk.END)
                self._meta_text.insert(tk.END, str(exc))
        elif current == "labels.tsv":
            try:
                self._labels_text.delete("1.0", tk.END)
                self._labels_text.insert(tk.END, self._service.load_labels_tsv())
            except UIDataLoadError as exc:
                self._labels_text.delete("1.0", tk.END)
                self._labels_text.insert(tk.END, str(exc))


if __name__ == "__main__":
    root = tk.Tk()
    app = UIApp(root)
    root.mainloop()
