"""
Custom Exceptions für UserManagement Feature.

Klare Fehler-Semantik für bessere Error-Handling im Service.
"""


class UserManagementError(Exception):
    """Basis-Exception für UserManagement."""
    pass


class UserNotFoundError(UserManagementError):
    """User wurde nicht gefunden."""
    def __init__(self, identifier: str):
        super().__init__(f"User nicht gefunden: {identifier}")


class UserAlreadyExistsError(UserManagementError):
    """User existiert bereits."""
    def __init__(self, username: str):
        super().__init__(f"User '{username}' existiert bereits")


class PermissionDeniedError(UserManagementError):
    """Keine Berechtigung für diese Aktion."""
    def __init__(self, action: str):
        super().__init__(f"Keine Berechtigung für: {action}")


class InvalidPasswordError(UserManagementError):
    """Ungültiges Passwort."""
    def __init__(self):
        super().__init__("Ungültiges Passwort")
