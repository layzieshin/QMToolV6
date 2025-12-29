"""
Licensing Service - Main licensing service implementation.

Author: QMToolV6 Development Team
Version: 1.0.0
"""

import logging
from typing import Optional, Tuple

from licensing.MODELS.dto.entitlements_dto import EntitlementsDTO
from licensing.MODELS.dto.verification_result_dto import LicenseVerificationResultDTO
from licensing.MODELS.enums.license_status import LicenseStatus
from licensing.MODELS.enums.license_error_code import LicenseErrorCode
from licensing.LOGIC.interfaces.licensing_service_interface import LicensingServiceInterface
from licensing.LOGIC.interfaces.license_backend_interface import LicenseBackendInterface
from licensing.LOGIC.interfaces.machine_fingerprint_provider_interface import MachineFingerprintProviderInterface

logger = logging.getLogger(__name__)


class LicensingService(LicensingServiceInterface):
    """
    Main licensing service.
    
    Coordinates license loading, verification, and entitlement checks.
    """
    
    def __init__(
        self,
        backend: LicenseBackendInterface,
        fingerprint_provider: MachineFingerprintProviderInterface
    ):
        """
        Initialize licensing service.
        
        Args:
            backend: License backend (file or online)
            fingerprint_provider: Machine fingerprint provider
        """
        self.backend = backend
        self.fingerprint_provider = fingerprint_provider
        
        # Cache verification result and entitlements
        self._verification_result: Optional[LicenseVerificationResultDTO] = None
        self._entitlements: Optional[EntitlementsDTO] = None
        
        # Initialize on startup
        self._initialize()
        
        logger.info("LicensingService initialized")
    
    def _initialize(self) -> None:
        """Initialize service by loading and verifying license."""
        try:
            # Get machine fingerprint
            machine_fp = self.fingerprint_provider.get_fingerprint_hash()
            logger.info(f"Machine fingerprint: {machine_fp[:20]}...")
            
            # Load license
            license_dto = self.backend.load_license()
            
            if license_dto is None:
                self._verification_result = LicenseVerificationResultDTO(
                    status=LicenseStatus.MISSING,
                    error_code=LicenseErrorCode.LICENSE_MISSING,
                    message="License file not found",
                    license_id=None
                )
                self._entitlements = EntitlementsDTO(features={})
                logger.warning("No license found - running with no entitlements")
                return
            
            # Verify license
            self._verification_result = self.backend.verify(license_dto, machine_fp)
            
            # Extract entitlements (even if invalid, for logging)
            if self._verification_result.is_valid():
                self._entitlements = self.backend.get_entitlements(license_dto)
                logger.info(
                    f"License verified successfully: {license_dto.license_id}, "
                    f"entitlements: {self._entitlements.get_entitled_features()}"
                )
            else:
                self._entitlements = EntitlementsDTO(features={})
                logger.warning(
                    f"License verification failed: {self._verification_result.message}"
                )
                
        except Exception as e:
            logger.error(f"Error initializing licensing service: {e}")
            self._verification_result = LicenseVerificationResultDTO(
                status=LicenseStatus.INVALID_FORMAT,
                error_code=LicenseErrorCode.LICENSE_INVALID_FORMAT,
                message=f"Error loading license: {str(e)}",
                license_id=None
            )
            self._entitlements = EntitlementsDTO(features={})
    
    def get_verification(self) -> LicenseVerificationResultDTO:
        """
        Get current license verification status.
        
        Returns:
            LicenseVerificationResultDTO with current status
        """
        if self._verification_result is None:
            # Should not happen, but handle gracefully
            return LicenseVerificationResultDTO(
                status=LicenseStatus.MISSING,
                error_code=LicenseErrorCode.LICENSE_MISSING,
                message="License not initialized",
                license_id=None
            )
        return self._verification_result
    
    def get_entitlements(self) -> EntitlementsDTO:
        """
        Get current license entitlements.
        
        Returns:
            EntitlementsDTO with feature entitlements
            (empty if no valid license)
        """
        if self._entitlements is None:
            return EntitlementsDTO(features={})
        return self._entitlements
    
    def is_feature_allowed(
        self,
        feature_code: str
    ) -> Tuple[bool, Optional[LicenseErrorCode]]:
        """
        Check if a feature is allowed based on license.
        
        Args:
            feature_code: Feature code to check
            
        Returns:
            Tuple of (allowed: bool, error_code: Optional[LicenseErrorCode])
        """
        # If no valid license, deny
        if not self._verification_result or not self._verification_result.is_valid():
            return (False, LicenseErrorCode.LICENSE_MISSING)
        
        # Check entitlement
        if not self._entitlements or not self._entitlements.is_entitled(feature_code):
            return (False, LicenseErrorCode.FEATURE_NOT_ENTITLED)
        
        return (True, None)
    
    def refresh_license(self) -> None:
        """
        Refresh license from backend.
        
        Re-loads and re-verifies license.
        """
        logger.info("Refreshing license...")
        self.backend.refresh()
        self._initialize()
