"""Authenticator-spezifische Exceptions."""


class AuthenticatorException(Exception):
    """Basis-Exception für Authenticator-Fehler."""
    pass


class InvalidCredentialsException(AuthenticatorException):
    """Exception wenn Login-Daten ungültig sind."""
    pass


class SessionNotFoundException(AuthenticatorException):
    """Exception wenn Session nicht gefunden wurde."""
    pass


class SessionExpiredException(AuthenticatorException):
    """Exception wenn Session abgelaufen ist."""
    pass


class UserNotAuthenticatedException(AuthenticatorException):
    """Exception wenn Benutzer nicht authentifiziert ist."""
    pass


class PasswordHashingException(AuthenticatorException):
    """Exception bei Passwort-Hashing-Fehlern."""
    pass
