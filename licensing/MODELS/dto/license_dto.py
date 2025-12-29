"""
License DTO - Data transfer object for license information.

Author: QMToolV6 Development Team
Version: 1.0.0
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass(frozen=True)
class LicenseDTO:
    """
    License data transfer object.
    
    Represents a QMTool license with entitlements and fingerprints.
    
    Attributes:
        schema: Schema version (e.g., "qmtool-license-v1")
        license_id: Unique license identifier
        customer: Customer name
        issued_at: Issue date (ISO format)
        valid_until: Expiration date (ISO format)
        allowed_fingerprints: List of allowed machine fingerprints (hex:sha256)
        entitlements: Feature entitlements (feature_code -> bool)
        signature: License signature (b64:...)
    
    Example:
        >>> license_dto = LicenseDTO(
        ...     schema="qmtool-license-v1",
        ...     license_id="LIC-2025-000123",
        ...     customer="Immunologikum",
        ...     issued_at="2025-12-29",
        ...     valid_until="2026-12-31",
        ...     allowed_fingerprints=["hex:9f2c...a1"],
        ...     entitlements={"translation": True, "audittrail": True},
        ...     signature="b64:MEUCIQ..."
        ... )
    """
    
    schema: str
    """Schema version identifier."""
    
    license_id: str
    """Unique license identifier."""
    
    customer: str
    """Customer name."""
    
    issued_at: str
    """Issue date in ISO format."""
    
    valid_until: str
    """Expiration date in ISO format."""
    
    allowed_fingerprints: List[str] = field(default_factory=list)
    """List of allowed machine fingerprints."""
    
    entitlements: Dict[str, bool] = field(default_factory=dict)
    """Feature entitlements mapping."""
    
    signature: str = ""
    """License signature."""
