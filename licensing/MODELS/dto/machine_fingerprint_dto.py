"""
Machine Fingerprint DTO - Hardware fingerprint information.

Author: QMToolV6 Development Team
Version: 1.0.0
"""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class MachineFingerprintDTO:
    """
    Machine fingerprint DTO.
    
    Contains hardware identifiers for machine fingerprinting.
    
    Attributes:
        machine_guid: Windows MachineGuid from registry
        bios_uuid: BIOS UUID from WMI
        baseboard_serial: Baseboard serial number (optional)
        canonical_string: Canonical fingerprint string
        hash: SHA256 hash of canonical string (hex:...)
    
    Example:
        >>> fp = MachineFingerprintDTO(
        ...     machine_guid="abc-123",
        ...     bios_uuid="uuid-456",
        ...     baseboard_serial="SN789",
        ...     canonical_string="MG=abc-123|UUID=uuid-456|MB=SN789",
        ...     hash="hex:9f2c...a1"
        ... )
    """
    
    machine_guid: Optional[str]
    """Windows MachineGuid from registry."""
    
    bios_uuid: Optional[str]
    """BIOS UUID from WMI."""
    
    baseboard_serial: Optional[str]
    """Baseboard serial number."""
    
    canonical_string: str
    """Canonical fingerprint string."""
    
    hash: str
    """SHA256 hash with hex: prefix."""
