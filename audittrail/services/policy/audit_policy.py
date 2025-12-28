"""
AuditTrail Policy

Zugriffskontrolle für Audit-Logs.
Definiert, wer welche Logs lesen/exportieren darf.

Design Principles:
- Keine Abhängigkeit zu UserManagement/Authenticator
- Erweiterbar für Rollen-Checks
- Transparent (klare Regeln)

Author: QMToolV6 Development Team
Version: 1.0.0
"""
from typing import Optional

from audittrail.dto.audit_dto import AuditLogFilterDTO


class AuditPolicy:
    """
    Policy für Zugriffskontrolle auf Audit-Logs.

    Regeln:
    - Jeder User kann eigene Logs lesen
    - Nur Admin/QMB kann alle Logs lesen
    - Nur Admin/QMB kann Logs exportieren
    - System-User (ID=0) hat vollen Zugriff

    Note:
        Aktuell Placeholder - später Integration mit UserManagement/Roles.
    """

    def __init__(self):
        """Initialisiert Policy."""
        # TODO: Integration mit UserManagement/Roles
        # Aktuell: Hardcoded Admin-IDs (später aus DB)
        self._admin_user_ids = [1]  # Vorläufig
        self._qmb_user_ids = [2]    # Vorläufig

    def can_read_logs(
        self,
        user_id: int,
        filters: Optional[AuditLogFilterDTO] = None
    ) -> bool:
        """
        Prüft, ob User Logs lesen darf.

        Args:
            user_id: ID des anfragenden Users
            filters: Optionale Filter (wenn user_id-Filter gesetzt, muss User eigene ID sein)

        Returns:
            True wenn erlaubt

        Rules:
            - System-User (0): Immer erlaubt
            - Admin/QMB: Immer erlaubt
            - Normaler User: Nur eigene Logs (filter.user_id == user_id)

        Example:
            >>> policy.can_read_logs(42, AuditLogFilterDTO(user_id=42))  # True
            >>> policy.can_read_logs(42, AuditLogFilterDTO(user_id=99))  # False
        """
        # System-User hat vollen Zugriff
        if user_id == 0:
            return True

        # Admin/QMB hat vollen Zugriff
        if self._is_admin_or_qmb(user_id):
            return True

        # Normaler User: Nur eigene Logs
        if filters and filters.user_id is not None:
            return filters.user_id == user_id

        # Wenn kein user_id-Filter: Nur Admin/QMB darf alle Logs sehen
        return False

    def can_export_logs(self, user_id: int) -> bool:
        """
        Prüft, ob User Logs exportieren darf.

        Args:
            user_id: ID des anfragenden Users

        Returns:
            True wenn erlaubt (nur Admin/QMB)

        Example:
            >>> policy.can_export_logs(1)  # True (Admin)
            >>> policy.can_export_logs(42)  # False (normaler User)
        """
        return user_id == 0 or self._is_admin_or_qmb(user_id)

    def _is_admin_or_qmb(self, user_id: int) -> bool:
        """Prüft, ob User Admin oder QMB ist."""
        # TODO: Integration mit UserManagement/Roles
        # Aktuell: Hardcoded IDs
        return user_id in self._admin_user_ids or user_id in self._qmb_user_ids
