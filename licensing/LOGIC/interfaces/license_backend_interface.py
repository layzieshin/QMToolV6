"""
License Backend Interface.

Author: QMToolV6 Development Team
Version: 1.0.0
"""

from abc import ABC, abstractmethod
from typing import Optional

from licensing.MODELS.dto.license_dto import LicenseDTO
from licensing.MODELS.dto.entitlements_dto import EntitlementsDTO
from licensing.MODELS.dto.verification_result_dto import LicenseVerificationResultDTO


class LicenseBackendInterface(ABC):
    """
    Interface for license backend operations.
    
    Supports both offline (file-based) and online (future) backends.
    """
    
    @abstractmethod
    def load_license(self) -> Optional[LicenseDTO]:
        """
        Load license from backend.
        
        Returns:
            LicenseDTO if found, None otherwise
        """
        pass
    
    @abstractmethod
    def verify(self, license_dto: LicenseDTO, machine_fp: str) -> LicenseVerificationResultDTO:
        """
        Verify license signature, expiry, and fingerprint.
        
        Args:
            license_dto: License to verify
            machine_fp: Machine fingerprint hash (hex:...)
            
        Returns:
            LicenseVerificationResultDTO with verification result
        """
        pass
    
    @abstractmethod
    def get_entitlements(self, license_dto: LicenseDTO) -> EntitlementsDTO:
        """
        Extract entitlements from license.
        
        Args:
            license_dto: License to extract from
            
        Returns:
            EntitlementsDTO with feature entitlements
        """
        pass
    
    @abstractmethod
    def refresh(self) -> None:
        """
        Refresh license from backend.
        
        For offline: no-op
        For online: re-fetch from server
        """
        pass
