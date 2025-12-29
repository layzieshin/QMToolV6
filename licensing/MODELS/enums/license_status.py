"""
License Status Enum - Status of license verification.

Author: QMToolV6 Development Team
Version: 1.0.0
"""

from enum import Enum


class LicenseStatus(Enum):
    """License verification status."""
    
    VALID = "VALID"
    """License is valid and all checks passed."""
    
    MISSING = "MISSING"
    """License file not found."""
    
    INVALID_FORMAT = "INVALID_FORMAT"
    """License file has invalid format or structure."""
    
    INVALID_SIGNATURE = "INVALID_SIGNATURE"
    """License signature verification failed."""
    
    EXPIRED = "EXPIRED"
    """License has expired."""
    
    FINGERPRINT_MISMATCH = "FINGERPRINT_MISMATCH"
    """Machine fingerprint does not match allowed fingerprints."""
