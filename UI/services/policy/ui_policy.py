"""Policies for UI input validation."""
from __future__ import annotations

import re

from UI.exceptions.ui_exceptions import UIValidationError


class UIPolicy:
    """Validates UI inputs."""

    _USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9_.-]{3,50}$")

    @staticmethod
    def validate_login(username: str, password: str) -> None:
        """Validate login inputs."""
        if not username or not password:
            raise UIValidationError("Username und Passwort sind erforderlich")
        if not UIPolicy._USERNAME_PATTERN.match(username):
            raise UIValidationError("Username muss 3-50 Zeichen lang sein")

    @staticmethod
    def validate_registration(username: str, password: str, email: str | None) -> None:
        """Validate registration inputs."""
        UIPolicy.validate_login(username, password)
        if len(password) < 8:
            raise UIValidationError("Passwort muss mindestens 8 Zeichen lang sein")
        if email is not None and "@" not in email:
            raise UIValidationError("E-Mail-Adresse ist ungültig")
