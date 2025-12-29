"""
End-to-end test for licensing flow with configurator.

Author: QMToolV6 Development Team
Version: 1.0.0
"""

import json
import pytest
from pathlib import Path
from datetime import datetime, timedelta

from licensing.LOGIC.util.bootstrap_example import ApplicationBootstrap
from licensing.LOGIC.crypto.signature_verifier import SignatureVerifier
from licensing.LOGIC.fingerprint.windows_fingerprint_provider import WindowsFingerprintProvider
from licensing.LOGIC.util.canonical_json import to_canonical_json


class TestLicensingEndToEnd:
    """End-to-end tests for licensing flow."""
    
    @pytest.fixture
    def test_project_root(self, tmp_path):
        """Create a temporary project structure."""
        # Create features directory structure
        features_root = tmp_path
        
        # Create licensing feature (core)
        licensing_dir = features_root / "licensing"
        licensing_dir.mkdir()
        licensing_meta = {
            "id": "licensing",
            "label": "Licensing",
            "version": "1.0.0",
            "main_class": "licensing.LOGIC.services.licensing_service.LicensingService",
            "is_core": True,
            "sort_order": 0,
            "requires_login": False,
            "dependencies": [],
            "configuration": {
                "license_path": str(tmp_path / "test_license.qmlic")
            }
        }
        with open(licensing_dir / "meta.json", 'w') as f:
            json.dump(licensing_meta, f, indent=2)
        
        # Create translation feature (requires license)
        translation_dir = features_root / "translation"
        translation_dir.mkdir()
        translation_meta = {
            "id": "translation",
            "label": "Translation",
            "version": "1.0.0",
            "main_class": "translation.services.translation_service.TranslationService",
            "is_core": False,
            "sort_order": 10,
            "requires_login": True,
            "dependencies": [],
            "licensing": {
                "requires_license": True,
                "feature_code": "translation",
                "enforcement": "registry"
            }
        }
        with open(translation_dir / "meta.json", 'w') as f:
            json.dump(translation_meta, f, indent=2)
        
        # Create audittrail feature (requires license)
        audit_dir = features_root / "audittrail"
        audit_dir.mkdir()
        audit_meta = {
            "id": "audittrail",
            "label": "Audit Trail",
            "version": "1.0.0",
            "main_class": "audittrail.services.audit_service.AuditService",
            "is_core": False,
            "sort_order": 3,
            "requires_login": True,
            "dependencies": [],
            "licensing": {
                "requires_license": True,
                "feature_code": "audittrail",
                "enforcement": "registry"
            }
        }
        with open(audit_dir / "meta.json", 'w') as f:
            json.dump(audit_meta, f, indent=2)
        
        return tmp_path
    
    def create_valid_license(
        self,
        license_path: Path,
        entitlements: dict
    ):
        """Create a valid license file."""
        # Get machine fingerprint
        fp_provider = WindowsFingerprintProvider()
        machine_fp = fp_provider.get_fingerprint_hash()
        
        # Create license data
        tomorrow = datetime.now() + timedelta(days=365)
        license_data = {
            "schema": "qmtool-license-v1",
            "license_id": "LIC-2025-E2E-TEST",
            "customer": "E2E Test Customer",
            "issued_at": datetime.now().isoformat()[:10],
            "valid_until": tomorrow.isoformat()[:10],
            "allowed_fingerprints": [machine_fp],
            "entitlements": entitlements
        }
        
        # Sign the license
        verifier = SignatureVerifier()
        canonical = to_canonical_json(license_data, exclude_keys=["signature"])
        signature = verifier.sign(canonical)
        license_data["signature"] = signature
        
        # Write to file
        with open(license_path, 'w', encoding='utf-8') as f:
            json.dump(license_data, f, indent=2)
    
    def test_bootstrap_with_valid_license(self, test_project_root):
        """Test application bootstrap with valid license."""
        # Create license with translation entitlement
        license_path = test_project_root / "test_license.qmlic"
        self.create_valid_license(
            license_path,
            {"translation": True, "audittrail": False}
        )
        
        # Bootstrap application
        bootstrap = ApplicationBootstrap(str(test_project_root))
        results = bootstrap.bootstrap()
        
        # Verify licensing is active and valid
        assert results["licensing_active"] is True
        assert results["license_valid"] is True
        
        # Verify features
        allowed_ids = {f.id for f in results["allowed_features"]}
        blocked_ids = {f.id for f in results["blocked_features"]}
        
        # Core features should be allowed
        assert "licensing" in allowed_ids
        
        # Translation should be allowed (entitled)
        assert "translation" in allowed_ids
        
        # AuditTrail should be blocked (not entitled)
        assert "audittrail" in blocked_ids
    
    def test_bootstrap_without_license(self, test_project_root):
        """Test application bootstrap without license file."""
        # Don't create license file
        
        # Bootstrap application
        bootstrap = ApplicationBootstrap(str(test_project_root))
        results = bootstrap.bootstrap()
        
        # Verify licensing is active but invalid
        assert results["licensing_active"] is True
        assert results["license_valid"] is False
        
        # Verify features
        allowed_ids = {f.id for f in results["allowed_features"]}
        blocked_ids = {f.id for f in results["blocked_features"]}
        
        # Core features should still be allowed
        assert "licensing" in allowed_ids
        
        # Licensed features should be blocked
        assert "translation" in blocked_ids
        assert "audittrail" in blocked_ids
    
    def test_bootstrap_with_all_entitlements(self, test_project_root):
        """Test application bootstrap with all features entitled."""
        # Create license with all entitlements
        license_path = test_project_root / "test_license.qmlic"
        self.create_valid_license(
            license_path,
            {"translation": True, "audittrail": True}
        )
        
        # Bootstrap application
        bootstrap = ApplicationBootstrap(str(test_project_root))
        results = bootstrap.bootstrap()
        
        # Verify all features are allowed
        allowed_ids = {f.id for f in results["allowed_features"]}
        
        assert "licensing" in allowed_ids
        assert "translation" in allowed_ids
        assert "audittrail" in allowed_ids
        
        # No features should be blocked
        assert len(results["blocked_features"]) == 0
