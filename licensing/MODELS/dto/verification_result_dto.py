"""
License Verification Result DTO - Result of license verification.

Author: QMToolV6 Development Team
Version: 1.0.0
"""

from dataclasses import dataclass
from typing import Optional

from licensing.MODELS.enums.license_status import LicenseStatus
from licensing.MODELS.enums.license_error_code import LicenseErrorCode


@dataclass(frozen=True)
class LicenseVerificationResultDTO:
    """
    License verification result DTO.
    
    Contains the result of license verification including status and errors.
    
    Attributes:
        status: License status
        error_code: Error code if verification failed
        message: Human-readable message
        license_id: License ID (if available)
    
    Example:
        >>> result = LicenseVerificationResultDTO(
        ...     status=LicenseStatus.VALID,
        ...     error_code=None,
        ...     message="License is valid",
        ...     license_id="LIC-2025-000123"
        ... )
    """
    
    status: LicenseStatus
    """License verification status."""
    
    error_code: Optional[LicenseErrorCode]
    """Error code if verification failed."""
    
    message: str
    """Human-readable verification message."""
    
    license_id: Optional[str] = None
    """License ID if available."""
    
    def is_valid(self) -> bool:
        """
        Check if license verification was successful.
        
        Returns:
            True if status is VALID, False otherwise
        """
        return self.status == LicenseStatus.VALID
