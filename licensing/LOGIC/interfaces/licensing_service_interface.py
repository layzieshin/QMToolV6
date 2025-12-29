"""
Licensing Service Interface.

Author: QMToolV6 Development Team
Version: 1.0.0
"""

from abc import ABC, abstractmethod
from typing import Optional, Tuple

from licensing.MODELS.dto.entitlements_dto import EntitlementsDTO
from licensing.MODELS.dto.verification_result_dto import LicenseVerificationResultDTO
from licensing.MODELS.enums.license_error_code import LicenseErrorCode


class LicensingServiceInterface(ABC):
    """
    Interface for licensing service.
    
    Main service for license management and feature entitlement checks.
    """
    
    @abstractmethod
    def get_verification(self) -> LicenseVerificationResultDTO:
        """
        Get current license verification status.
        
        Returns:
            LicenseVerificationResultDTO with current status
        """
        pass
    
    @abstractmethod
    def get_entitlements(self) -> EntitlementsDTO:
        """
        Get current license entitlements.
        
        Returns:
            EntitlementsDTO with feature entitlements
            (empty if no valid license)
        """
        pass
    
    @abstractmethod
    def is_feature_allowed(self, feature_code: str) -> Tuple[bool, Optional[LicenseErrorCode]]:
        """
        Check if a feature is allowed based on license.
        
        Args:
            feature_code: Feature code to check
            
        Returns:
            Tuple of (allowed: bool, error_code: Optional[LicenseErrorCode])
        """
        pass
    
    @abstractmethod
    def refresh_license(self) -> None:
        """
        Refresh license from backend.
        
        Re-loads and re-verifies license.
        """
        pass
