"""
FeatureRegistryDTO - Registry-Eintrag für ein Feature.

Kapselt Feature-Descriptor plus Runtime-Status.

Author: QMToolV6 Development Team
Version: 1.0.0
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from configurator.dto.feature_descriptor_dto import FeatureDescriptorDTO
from configurator.enum.feature_status import FeatureStatus


@dataclass(frozen=True)
class FeatureRegistryDTO:
    """
    Registry-Eintrag für ein Feature (Descriptor + Status).

    MVP:  Alle Features haben status=ACTIVE, loaded=False (keine dynamische Ladung).
    Zukünftig: Features können DISABLED, LOADING, ERROR haben.

    Attributes:
        descriptor:  Vollständige Feature-Beschreibung aus meta.json
        status: Aktueller Status (ACTIVE, DISABLED, ERROR)
        loaded: Ob Service-Klasse bereits geladen wurde
        error: Fehlermeldung bei STATUS=ERROR
    """

    descriptor: FeatureDescriptorDTO
    """Vollständige Feature-Beschreibung aus meta.json."""

    status: FeatureStatus = FeatureStatus.ACTIVE
    """Aktueller Feature-Status (MVP: immer ACTIVE)."""

    loaded: bool = False
    """Ob Service-Klasse bereits instanziiert wurde (MVP: immer False)."""

    error: Optional[str] = None
    """Fehlermeldung falls status=ERROR (MVP: immer None)."""

    def is_available(self) -> bool:
        """
        Prüft, ob Feature verfügbar ist.

        Returns:
            True wenn status=ACTIVE und kein Error
        """
        return self.status == FeatureStatus.ACTIVE and self.error is None

    def get_feature_id(self) -> str:
        """
        Shortcut für Feature-ID.

        Returns:
            Feature-ID aus Descriptor
        """
        return self.descriptor.id