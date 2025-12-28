"""
FeatureDescriptorDTO - Vollständige Feature-Beschreibung. 

Repräsentiert alle Metadaten eines Features aus dessen meta.json.

Author: QMToolV6 Development Team
Version: 1.0.0
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, List

from configurator.dto.audit_config_dto import AuditConfigDTO


@dataclass(frozen=True)
class FeatureDescriptorDTO:
    """
    Feature-Beschreibung aus `<feature_id>/meta.json`.

    Pflichtfelder:
    - id:  Muss identisch mit Ordnernamen sein
    - label:  Anzeigename für UI
    - version:  Semantic Versioning (z.B. "1.0.0")
    - main_class: Vollqualifizierter Python-Pfad zur Service-Klasse

    Optionale Felder:
    - visible_for: Rollen-basierte Sichtbarkeit (None = alle)
    - is_core: Markiert Core-Features (nicht deaktivierbar)
    - sort_order: Sortierung in UI (niedriger = weiter oben)
    - requires_login: Ob Login erforderlich ist
    - dependencies: Liste anderer Feature-IDs, die benötigt werden
    - audit:  Audit-Konfiguration
    - description:  Beschreibungstext
    - icon: Icon-Name oder Pfad

    Beispiel meta.json:
        {
            "id":  "documentlifecycle",
            "label":  "Dokumentenmanagement",
            "version": "1.0.0",
            "main_class": "documentlifecycle.services. document_service.DocumentService",
            "visible_for": ["ADMIN", "USER", "QMB"],
            "is_core":  true,
            "sort_order": 10,
            "requires_login":  true,
            "dependencies": ["authenticator", "user_management"],
            "audit": {
                "must_audit": true,
                "min_log_level": "INFO",
                "critical_actions": ["SIGN_DOCUMENT"],
                "retention_days": 2555
            },
            "description": "Verwaltung von QM-Dokumenten",
            "icon": "document-icon.svg"
        }
    """

    # ===== Pflichtfelder =====
    id: str
    """Feature-ID (muss identisch mit Ordnernamen sein)."""

    label: str
    """Anzeigename für UI."""

    version: str
    """Semantic Versioning (z.B. "1.0.0")."""

    main_class: str
    """Vollqualifizierter Python-Pfad zur Service-Klasse."""

    # ===== Optionale Felder =====
    visible_for: List[str] = field(default_factory=list)
    """Rollen, die dieses Feature sehen dürfen (leer = alle)."""

    is_core: bool = False
    """Core-Features können nicht deaktiviert werden."""

    sort_order: int = 999
    """Sortierreihenfolge in UI (niedriger = weiter oben)."""

    requires_login: bool = True
    """Ob Login erforderlich ist, um Feature zu nutzen."""

    dependencies: List[str] = field(default_factory=list)
    """Liste von Feature-IDs, die vorab geladen sein müssen."""

    audit: Optional[AuditConfigDTO] = None
    """Audit-spezifische Konfiguration."""

    description: Optional[str] = None
    """Beschreibungstext für Tooltip/Hilfe."""

    icon: Optional[str] = None
    """Icon-Name oder Pfad."""

    def is_visible_for_role(self, role: str) -> bool:
        """
        Prüft, ob Feature für gegebene Rolle sichtbar ist.

        Args:
            role:  Rollenname (z.B. "ADMIN", "USER")

        Returns:
            True wenn sichtbar (visible_for ist leer oder role enthalten)
        """
        if not self.visible_for:
            return True
        return role.upper() in [r.upper() for r in self.visible_for]

    def has_dependency(self, feature_id: str) -> bool:
        """
        Prüft, ob Feature von anderem Feature abhängt.

        Args:
            feature_id: ID des zu prüfenden Features

        Returns:
            True wenn Abhängigkeit besteht
        """
        return feature_id in self.dependencies