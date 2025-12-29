"""
Tests for licensing DTOs and enums.

Author: QMToolV6 Development Team
Version: 1.0.0
"""

import pytest

from licensing.MODELS.enums.license_status import LicenseStatus
from licensing.MODELS.enums.license_error_code import LicenseErrorCode
from licensing.MODELS.dto.license_dto import LicenseDTO
from licensing.MODELS.dto.entitlements_dto import EntitlementsDTO
from licensing.MODELS.dto.machine_fingerprint_dto import MachineFingerprintDTO
from licensing.MODELS.dto.verification_result_dto import LicenseVerificationResultDTO
from licensing.MODELS.dto.gate_decision_dto import GateDecisionDTO


class TestLicenseEnums:
    """Test license enums."""
    
    def test_license_status_values(self):
        """Test LicenseStatus enum values."""
        assert LicenseStatus.VALID.value == "VALID"
        assert LicenseStatus.MISSING.value == "MISSING"
        assert LicenseStatus.INVALID_FORMAT.value == "INVALID_FORMAT"
        assert LicenseStatus.INVALID_SIGNATURE.value == "INVALID_SIGNATURE"
        assert LicenseStatus.EXPIRED.value == "EXPIRED"
        assert LicenseStatus.FINGERPRINT_MISMATCH.value == "FINGERPRINT_MISMATCH"
    
    def test_license_error_code_values(self):
        """Test LicenseErrorCode enum values."""
        assert LicenseErrorCode.LICENSE_MISSING.value == "LICENSE_MISSING"
        assert LicenseErrorCode.FEATURE_NOT_ENTITLED.value == "FEATURE_NOT_ENTITLED"


class TestLicenseDTO:
    """Test LicenseDTO."""
    
    def test_create_license_dto(self):
        """Test creating LicenseDTO."""
        license_dto = LicenseDTO(
            schema="qmtool-license-v1",
            license_id="LIC-2025-000123",
            customer="Immunologikum",
            issued_at="2025-12-29",
            valid_until="2026-12-31",
            allowed_fingerprints=["hex:abc123"],
            entitlements={"translation": True},
            signature="b64:signature"
        )
        
        assert license_dto.schema == "qmtool-license-v1"
        assert license_dto.license_id == "LIC-2025-000123"
        assert license_dto.customer == "Immunologikum"
        assert "translation" in license_dto.entitlements


class TestEntitlementsDTO:
    """Test EntitlementsDTO."""
    
    def test_is_entitled(self):
        """Test is_entitled method."""
        entitlements = EntitlementsDTO(
            features={"translation": True, "audittrail": True, "other": False}
        )
        
        assert entitlements.is_entitled("translation") is True
        assert entitlements.is_entitled("audittrail") is True
        assert entitlements.is_entitled("other") is False
        assert entitlements.is_entitled("unknown") is False
    
    def test_get_entitled_features(self):
        """Test get_entitled_features method."""
        entitlements = EntitlementsDTO(
            features={"translation": True, "audittrail": True, "other": False}
        )
        
        entitled = entitlements.get_entitled_features()
        assert "translation" in entitled
        assert "audittrail" in entitled
        assert "other" not in entitled


class TestMachineFingerprintDTO:
    """Test MachineFingerprintDTO."""
    
    def test_create_fingerprint_dto(self):
        """Test creating MachineFingerprintDTO."""
        fp = MachineFingerprintDTO(
            machine_guid="abc-123",
            bios_uuid="uuid-456",
            baseboard_serial="SN789",
            canonical_string="MG=abc-123|UUID=uuid-456|MB=SN789",
            hash="hex:9f2c...a1"
        )
        
        assert fp.machine_guid == "abc-123"
        assert fp.bios_uuid == "uuid-456"
        assert fp.canonical_string == "MG=abc-123|UUID=uuid-456|MB=SN789"
        assert fp.hash == "hex:9f2c...a1"


class TestVerificationResultDTO:
    """Test LicenseVerificationResultDTO."""
    
    def test_is_valid_true(self):
        """Test is_valid returns True for VALID status."""
        result = LicenseVerificationResultDTO(
            status=LicenseStatus.VALID,
            error_code=None,
            message="License is valid",
            license_id="LIC-123"
        )
        
        assert result.is_valid() is True
    
    def test_is_valid_false(self):
        """Test is_valid returns False for non-VALID status."""
        result = LicenseVerificationResultDTO(
            status=LicenseStatus.EXPIRED,
            error_code=LicenseErrorCode.LICENSE_EXPIRED,
            message="License expired",
            license_id="LIC-123"
        )
        
        assert result.is_valid() is False


class TestGateDecisionDTO:
    """Test GateDecisionDTO."""
    
    def test_allowed_decision(self):
        """Test allowed gate decision."""
        decision = GateDecisionDTO(
            allowed=True,
            feature_code="translation",
            reason="Feature is entitled",
            error_code=None
        )
        
        assert decision.allowed is True
        assert decision.feature_code == "translation"
        assert decision.error_code is None
    
    def test_denied_decision(self):
        """Test denied gate decision."""
        decision = GateDecisionDTO(
            allowed=False,
            feature_code="translation",
            reason="Not entitled",
            error_code=LicenseErrorCode.FEATURE_NOT_ENTITLED
        )
        
        assert decision.allowed is False
        assert decision.error_code == LicenseErrorCode.FEATURE_NOT_ENTITLED
