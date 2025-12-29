"""
File License Repository - File-based license storage.

Author: QMToolV6 Development Team
Version: 1.0.0
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from licensing.MODELS.dto.license_dto import LicenseDTO
from licensing.MODELS.dto.entitlements_dto import EntitlementsDTO
from licensing.MODELS.dto.verification_result_dto import LicenseVerificationResultDTO
from licensing.MODELS.enums.license_status import LicenseStatus
from licensing.MODELS.enums.license_error_code import LicenseErrorCode
from licensing.LOGIC.interfaces.license_backend_interface import LicenseBackendInterface
from licensing.LOGIC.crypto.signature_verifier import SignatureVerifier
from licensing.LOGIC.util.canonical_json import to_canonical_json

logger = logging.getLogger(__name__)


class FileLicenseRepository(LicenseBackendInterface):
    """
    File-based license repository.
    
    Loads licenses from local file system and verifies them.
    """
    
    def __init__(
        self,
        license_path: Path,
        signature_verifier: SignatureVerifier
    ):
        """
        Initialize file license repository.
        
        Args:
            license_path: Path to license file
            signature_verifier: Signature verifier instance
        """
        self.license_path = license_path
        self.signature_verifier = signature_verifier
        logger.info(f"FileLicenseRepository initialized with path: {license_path}")
    
    def load_license(self) -> Optional[LicenseDTO]:
        """
        Load license from file.
        
        Returns:
            LicenseDTO if file exists and is valid JSON, None otherwise
        """
        if not self.license_path.exists():
            logger.warning(f"License file not found: {self.license_path}")
            return None
        
        try:
            with open(self.license_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Validate required fields
            required = ["schema", "license_id", "customer", "issued_at", "valid_until"]
            for field in required:
                if field not in data:
                    logger.error(f"License missing required field: {field}")
                    return None
            
            return LicenseDTO(
                schema=data["schema"],
                license_id=data["license_id"],
                customer=data["customer"],
                issued_at=data["issued_at"],
                valid_until=data["valid_until"],
                allowed_fingerprints=data.get("allowed_fingerprints", []),
                entitlements=data.get("entitlements", {}),
                signature=data.get("signature", "")
            )
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in license file: {e}")
            return None
        except Exception as e:
            logger.error(f"Error loading license: {e}")
            return None
    
    def verify(
        self,
        license_dto: LicenseDTO,
        machine_fp: str
    ) -> LicenseVerificationResultDTO:
        """
        Verify license signature, expiry, and fingerprint.
        
        Args:
            license_dto: License to verify
            machine_fp: Machine fingerprint hash (hex:...)
            
        Returns:
            LicenseVerificationResultDTO with verification result
        """
        # 1. Verify signature
        canonical = to_canonical_json(
            license_dto.__dict__,
            exclude_keys=["signature"]
        )
        
        if not self.signature_verifier.verify(canonical, license_dto.signature):
            return LicenseVerificationResultDTO(
                status=LicenseStatus.INVALID_SIGNATURE,
                error_code=LicenseErrorCode.LICENSE_INVALID_SIGNATURE,
                message="License signature verification failed",
                license_id=license_dto.license_id
            )
        
        # 2. Check expiry
        try:
            valid_until = datetime.fromisoformat(license_dto.valid_until)
            if datetime.now() > valid_until:
                return LicenseVerificationResultDTO(
                    status=LicenseStatus.EXPIRED,
                    error_code=LicenseErrorCode.LICENSE_EXPIRED,
                    message=f"License expired on {license_dto.valid_until}",
                    license_id=license_dto.license_id
                )
        except ValueError as e:
            logger.error(f"Invalid date format in license: {e}")
            return LicenseVerificationResultDTO(
                status=LicenseStatus.INVALID_FORMAT,
                error_code=LicenseErrorCode.LICENSE_INVALID_FORMAT,
                message="Invalid date format in license",
                license_id=license_dto.license_id
            )
        
        # 3. Check fingerprint
        if license_dto.allowed_fingerprints:
            if machine_fp not in license_dto.allowed_fingerprints:
                return LicenseVerificationResultDTO(
                    status=LicenseStatus.FINGERPRINT_MISMATCH,
                    error_code=LicenseErrorCode.LICENSE_FINGERPRINT_MISMATCH,
                    message="Machine fingerprint not in allowed list",
                    license_id=license_dto.license_id
                )
        
        # All checks passed
        return LicenseVerificationResultDTO(
            status=LicenseStatus.VALID,
            error_code=None,
            message="License is valid",
            license_id=license_dto.license_id
        )
    
    def get_entitlements(self, license_dto: LicenseDTO) -> EntitlementsDTO:
        """
        Extract entitlements from license.
        
        Args:
            license_dto: License to extract from
            
        Returns:
            EntitlementsDTO with feature entitlements
        """
        return EntitlementsDTO(features=license_dto.entitlements)
    
    def refresh(self) -> None:
        """
        Refresh license (no-op for file backend).
        """
        logger.debug("Refresh called on file backend (no-op)")
