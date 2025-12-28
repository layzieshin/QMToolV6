from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, List


@dataclass(frozen=True)
class AuditConfigDTO:
    """Audit-spezifische Feature-Konfiguration (aus meta.json)."""

    must_audit: bool = False
    min_log_level: str = "INFO"
    critical_actions: Optional[List[str]] = None
    retention_days: int = 365
