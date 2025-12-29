"""
Tests for feature gatekeeper.

Author: QMToolV6 Development Team
Version: 1.0.0
"""

import pytest

from licensing.MODELS.dto.entitlements_dto import EntitlementsDTO
from licensing.MODELS.enums.license_error_code import LicenseErrorCode
from licensing.LOGIC.services.feature_gatekeeper import FeatureGatekeeper


class TestFeatureGatekeeper:
    """Test FeatureGatekeeper."""
    
    @pytest.fixture
    def gatekeeper(self):
        """Create gatekeeper instance."""
        return FeatureGatekeeper()
    
    @pytest.fixture
    def entitlements_with_translation(self):
        """Create entitlements with translation enabled."""
        return EntitlementsDTO(features={"translation": True})
    
    @pytest.fixture
    def empty_entitlements(self):
        """Create empty entitlements."""
        return EntitlementsDTO(features={})
    
    def test_core_feature_always_allowed(self, gatekeeper, empty_entitlements):
        """Test that core features are always allowed."""
        meta = {
            "id": "licensing",
            "is_core": True
        }
        
        decision = gatekeeper.check_feature(meta, empty_entitlements)
        
        assert decision.allowed is True
        assert decision.error_code is None
        assert "core" in decision.reason.lower()
    
    def test_feature_without_license_requirement_allowed(
        self,
        gatekeeper,
        empty_entitlements
    ):
        """Test that features not requiring license are allowed."""
        meta = {
            "id": "test_feature",
            "is_core": False,
            "licensing": {
                "requires_license": False
            }
        }
        
        decision = gatekeeper.check_feature(meta, empty_entitlements)
        
        assert decision.allowed is True
        assert decision.error_code is None
    
    def test_feature_with_valid_entitlement_allowed(
        self,
        gatekeeper,
        entitlements_with_translation
    ):
        """Test that entitled features are allowed."""
        meta = {
            "id": "translation",
            "is_core": False,
            "licensing": {
                "requires_license": True,
                "feature_code": "translation"
            }
        }
        
        decision = gatekeeper.check_feature(meta, entitlements_with_translation)
        
        assert decision.allowed is True
        assert decision.error_code is None
        assert decision.feature_code == "translation"
    
    def test_feature_without_entitlement_denied(
        self,
        gatekeeper,
        empty_entitlements
    ):
        """Test that non-entitled features are denied."""
        meta = {
            "id": "translation",
            "is_core": False,
            "licensing": {
                "requires_license": True,
                "feature_code": "translation"
            }
        }
        
        decision = gatekeeper.check_feature(meta, empty_entitlements)
        
        assert decision.allowed is False
        assert decision.error_code == LicenseErrorCode.FEATURE_NOT_ENTITLED
        assert decision.feature_code == "translation"
    
    def test_feature_with_missing_feature_code_denied(
        self,
        gatekeeper,
        entitlements_with_translation
    ):
        """Test that features with missing feature_code are denied."""
        meta = {
            "id": "test_feature",
            "is_core": False,
            "licensing": {
                "requires_license": True
                # missing feature_code
            }
        }
        
        decision = gatekeeper.check_feature(meta, entitlements_with_translation)
        
        assert decision.allowed is False
        assert decision.error_code == LicenseErrorCode.FEATURE_META_INVALID
    
    def test_feature_with_invalid_feature_code_denied(
        self,
        gatekeeper,
        entitlements_with_translation
    ):
        """Test that features with invalid feature_code format are denied."""
        meta = {
            "id": "test_feature",
            "is_core": False,
            "licensing": {
                "requires_license": True,
                "feature_code": "INVALID-CODE!"  # Invalid format
            }
        }
        
        decision = gatekeeper.check_feature(meta, entitlements_with_translation)
        
        assert decision.allowed is False
        assert decision.error_code == LicenseErrorCode.FEATURE_META_INVALID
