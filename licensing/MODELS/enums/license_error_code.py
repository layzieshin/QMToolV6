"""
License Error Code Enum - Error codes for licensing system.

Author: QMToolV6 Development Team
Version: 1.0.0
"""

from enum import Enum


class LicenseErrorCode(Enum):
    """License error codes."""
    
    LICENSE_MISSING = "LICENSE_MISSING"
    """License file not found."""
    
    LICENSE_INVALID_FORMAT = "LICENSE_INVALID_FORMAT"
    """License file has invalid format."""
    
    LICENSE_INVALID_SIGNATURE = "LICENSE_INVALID_SIGNATURE"
    """License signature is invalid."""
    
    LICENSE_EXPIRED = "LICENSE_EXPIRED"
    """License has expired."""
    
    LICENSE_FINGERPRINT_MISMATCH = "LICENSE_FINGERPRINT_MISMATCH"
    """Machine fingerprint mismatch."""
    
    FEATURE_NOT_ENTITLED = "FEATURE_NOT_ENTITLED"
    """Feature is not entitled in license."""
    
    FEATURE_META_INVALID = "FEATURE_META_INVALID"
    """Feature metadata is invalid."""
    
    FINGERPRINT_UNAVAILABLE = "FINGERPRINT_UNAVAILABLE"
    """Unable to retrieve machine fingerprint."""
