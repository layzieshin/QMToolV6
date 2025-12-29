"""
Integration tests for licensing service.

Author: QMToolV6 Development Team
Version: 1.0.0
"""

import json
import pytest
from pathlib import Path
from datetime import datetime, timedelta

from licensing.LOGIC.services.licensing_service import LicensingService
from licensing.LOGIC.repositories.file_license_repository import FileLicenseRepository
from licensing.LOGIC.crypto.signature_verifier import SignatureVerifier
from licensing.LOGIC.fingerprint.windows_fingerprint_provider import WindowsFingerprintProvider
from licensing.LOGIC.util.canonical_json import to_canonical_json
from licensing.MODELS.enums.license_status import LicenseStatus
from licensing.MODELS.enums.license_error_code import LicenseErrorCode


class TestLicensingServiceIntegration:
    """Integration tests for licensing service."""
    
    @pytest.fixture
    def temp_license_path(self, tmp_path):
        """Create temporary license file path."""
        return tmp_path / "test_license.qmlic"
    
    @pytest.fixture
    def fingerprint_provider(self):
        """Create fingerprint provider."""
        return WindowsFingerprintProvider()
    
    @pytest.fixture
    def signature_verifier(self):
        """Create signature verifier."""
        return SignatureVerifier()
    
    def create_valid_license(
        self,
        license_path: Path,
        fingerprint: str,
        entitlements: dict,
        signature_verifier: SignatureVerifier
    ):
        """Helper to create a valid license file."""
        # Create license data
        tomorrow = datetime.now() + timedelta(days=1)
        license_data = {
            "schema": "qmtool-license-v1",
            "license_id": "LIC-2025-TEST-001",
            "customer": "Test Customer",
            "issued_at": datetime.now().isoformat()[:10],
            "valid_until": tomorrow.isoformat()[:10],
            "allowed_fingerprints": [fingerprint],
            "entitlements": entitlements
        }
        
        # Sign the license
        canonical = to_canonical_json(license_data, exclude_keys=["signature"])
        signature = signature_verifier.sign(canonical)
        license_data["signature"] = signature
        
        # Write to file
        with open(license_path, 'w', encoding='utf-8') as f:
            json.dump(license_data, f, indent=2)
    
    def test_licensing_service_with_valid_license(
        self,
        temp_license_path,
        fingerprint_provider,
        signature_verifier
    ):
        """Test licensing service with valid license."""
        # Get machine fingerprint
        machine_fp = fingerprint_provider.get_fingerprint_hash()
        
        # Create valid license
        self.create_valid_license(
            temp_license_path,
            machine_fp,
            {"translation": True, "audittrail": True},
            signature_verifier
        )
        
        # Create backend and service
        backend = FileLicenseRepository(temp_license_path, signature_verifier)
        service = LicensingService(backend, fingerprint_provider)
        
        # Verify license status
        verification = service.get_verification()
        assert verification.status == LicenseStatus.VALID
        assert verification.is_valid()
        
        # Check entitlements
        entitlements = service.get_entitlements()
        assert entitlements.is_entitled("translation")
        assert entitlements.is_entitled("audittrail")
        
        # Check feature allowance
        allowed, error = service.is_feature_allowed("translation")
        assert allowed is True
        assert error is None
        
        allowed, error = service.is_feature_allowed("unknown_feature")
        assert allowed is False
        assert error == LicenseErrorCode.FEATURE_NOT_ENTITLED
    
    def test_licensing_service_with_missing_license(
        self,
        temp_license_path,
        fingerprint_provider,
        signature_verifier
    ):
        """Test licensing service with missing license."""
        # Don't create license file
        backend = FileLicenseRepository(temp_license_path, signature_verifier)
        service = LicensingService(backend, fingerprint_provider)
        
        # Verify license status
        verification = service.get_verification()
        assert verification.status == LicenseStatus.MISSING
        assert not verification.is_valid()
        
        # Check entitlements are empty
        entitlements = service.get_entitlements()
        assert not entitlements.is_entitled("translation")
    
    def test_licensing_service_with_expired_license(
        self,
        temp_license_path,
        fingerprint_provider,
        signature_verifier
    ):
        """Test licensing service with expired license."""
        # Get machine fingerprint
        machine_fp = fingerprint_provider.get_fingerprint_hash()
        
        # Create expired license
        yesterday = datetime.now() - timedelta(days=1)
        license_data = {
            "schema": "qmtool-license-v1",
            "license_id": "LIC-2025-EXPIRED",
            "customer": "Test Customer",
            "issued_at": "2024-01-01",
            "valid_until": yesterday.isoformat()[:10],
            "allowed_fingerprints": [machine_fp],
            "entitlements": {"translation": True}
        }
        
        canonical = to_canonical_json(license_data, exclude_keys=["signature"])
        signature = signature_verifier.sign(canonical)
        license_data["signature"] = signature
        
        with open(temp_license_path, 'w', encoding='utf-8') as f:
            json.dump(license_data, f, indent=2)
        
        # Create service
        backend = FileLicenseRepository(temp_license_path, signature_verifier)
        service = LicensingService(backend, fingerprint_provider)
        
        # Verify license status
        verification = service.get_verification()
        assert verification.status == LicenseStatus.EXPIRED
        assert not verification.is_valid()
    
    def test_licensing_service_with_fingerprint_mismatch(
        self,
        temp_license_path,
        fingerprint_provider,
        signature_verifier
    ):
        """Test licensing service with fingerprint mismatch."""
        # Create license with different fingerprint
        self.create_valid_license(
            temp_license_path,
            "hex:different_fingerprint_hash",
            {"translation": True},
            signature_verifier
        )
        
        # Create service
        backend = FileLicenseRepository(temp_license_path, signature_verifier)
        service = LicensingService(backend, fingerprint_provider)
        
        # Verify license status
        verification = service.get_verification()
        assert verification.status == LicenseStatus.FINGERPRINT_MISMATCH
        assert not verification.is_valid()
