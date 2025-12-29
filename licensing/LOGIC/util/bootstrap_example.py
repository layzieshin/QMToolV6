"""
Licensing Integration Example - How to integrate licensing with configurator.

This module demonstrates how the licensing gatekeeper should be integrated
into the application bootstrap process.

Author: QMToolV6 Development Team
Version: 1.0.0
"""

from pathlib import Path
from typing import List, Tuple
import logging

from configurator.services.configurator_service import ConfiguratorService
from configurator.repository.feature_repository import FeatureRepository
from configurator.repository.config_repository import ConfigRepository

from licensing.LOGIC.services.licensing_service import LicensingService
from licensing.LOGIC.services.feature_gatekeeper import FeatureGatekeeper
from licensing.LOGIC.repositories.file_license_repository import FileLicenseRepository
from licensing.LOGIC.crypto.signature_verifier import SignatureVerifier
from licensing.LOGIC.fingerprint.windows_fingerprint_provider import WindowsFingerprintProvider
from licensing.LOGIC.util.path_resolver import resolve_license_path

logger = logging.getLogger(__name__)


class ApplicationBootstrap:
    """
    Application bootstrap with licensing integration.
    
    Demonstrates the recommended flow for feature registration with
    license enforcement.
    """
    
    def __init__(self, project_root: str = "."):
        """
        Initialize application bootstrap.
        
        Args:
            project_root: Root directory of the project
        """
        self.project_root = Path(project_root)
        
        # Initialize configurator
        self.feature_repo = FeatureRepository(str(self.project_root))
        self.config_repo = ConfigRepository(str(self.project_root))
        self.configurator = ConfiguratorService(self.feature_repo, self.config_repo)
        
        # Initialize licensing (if licensing feature exists)
        self.licensing_service = None
        self.gatekeeper = None
        self._initialize_licensing()
    
    def _initialize_licensing(self) -> None:
        """
        Initialize licensing system.
        
        This should be done early in the boot process, before other
        features are registered.
        """
        try:
            # Check if licensing feature exists
            licensing_meta = self.configurator.get_feature_meta("licensing")
            logger.info(f"Found licensing feature: {licensing_meta.label}")
            
            # Get license path from configuration
            # For meta loaded from meta.json, we need to reload the raw dict
            import json
            meta_file = self.project_root / "licensing" / "meta.json"
            if meta_file.exists():
                with open(meta_file) as f:
                    raw_meta = json.load(f)
                    config = raw_meta.get("configuration", {})
                    license_path_template = config.get(
                        "license_path",
                        "%PROGRAMDATA%\\QMTool\\license.qmlic"
                    )
            else:
                license_path_template = "%PROGRAMDATA%\\QMTool\\license.qmlic"
            
            # If path looks like a test path (absolute), use it directly
            if Path(license_path_template).is_absolute() or not any(
                env_var in license_path_template for env_var in ["%", "$"]
            ):
                license_path = Path(license_path_template)
            else:
                license_path = resolve_license_path(license_path_template)
            
            logger.info(f"License path: {license_path}")
            
            # Initialize licensing components
            verifier = SignatureVerifier()
            fingerprint_provider = WindowsFingerprintProvider()
            backend = FileLicenseRepository(license_path, verifier)
            
            # Create licensing service
            self.licensing_service = LicensingService(backend, fingerprint_provider)
            
            # Create gatekeeper
            self.gatekeeper = FeatureGatekeeper()
            
            # Log license status
            verification = self.licensing_service.get_verification()
            if verification.is_valid():
                logger.info(
                    f"License verified: {verification.license_id}, "
                    f"entitlements: {self.licensing_service.get_entitlements().get_entitled_features()}"
                )
            else:
                logger.warning(
                    f"License verification failed: {verification.message}"
                )
                
        except Exception as e:
            logger.warning(f"Could not initialize licensing: {e}")
            logger.info("Running without licensing enforcement")
            self.licensing_service = None
            self.gatekeeper = None
    
    def discover_and_filter_features(self) -> Tuple[List, List]:
        """
        Discover all features and filter based on licensing.
        
        Returns:
            Tuple of (allowed_features, blocked_features)
        """
        # Discover all features
        all_features = self.configurator.discover_features()
        logger.info(f"Discovered {len(all_features)} features")
        
        if not self.gatekeeper or not self.licensing_service:
            # No licensing enforcement, allow all features
            logger.info("No licensing enforcement - allowing all features")
            return all_features, []
        
        # Get current entitlements
        entitlements = self.licensing_service.get_entitlements()
        
        # Separate features by core status first
        core_features = [f for f in all_features if f.is_core]
        non_core_features = [f for f in all_features if not f.is_core]
        
        logger.info(
            f"Found {len(core_features)} core features, "
            f"{len(non_core_features)} non-core features"
        )
        
        # Core features are always allowed
        allowed_features = core_features.copy()
        blocked_features = []
        
        # Check non-core features with gatekeeper
        for feature in non_core_features:
            # Convert FeatureDescriptorDTO to dict for gatekeeper
            meta = {
                "id": feature.id,
                "is_core": feature.is_core,
                "licensing": getattr(feature, "licensing", {})
            }
            
            # Note: Current FeatureDescriptorDTO doesn't have licensing field
            # This would need to be added to the DTO structure
            # For now, we check the raw meta.json
            try:
                import json
                meta_path = self.project_root / feature.id / "meta.json"
                if meta_path.exists():
                    with open(meta_path) as f:
                        raw_meta = json.load(f)
                        meta["licensing"] = raw_meta.get("licensing", {})
            except Exception as e:
                logger.warning(f"Could not load licensing config for {feature.id}: {e}")
            
            # Check with gatekeeper
            decision = self.gatekeeper.check_feature(meta, entitlements)
            
            if decision.allowed:
                allowed_features.append(feature)
                logger.info(f"Feature allowed: {feature.id} - {decision.reason}")
            else:
                blocked_features.append(feature)
                logger.warning(
                    f"Feature blocked: {feature.id} - {decision.reason} "
                    f"(error: {decision.error_code})"
                )
        
        logger.info(
            f"Feature registration results: {len(allowed_features)} allowed, "
            f"{len(blocked_features)} blocked"
        )
        
        return allowed_features, blocked_features
    
    def bootstrap(self) -> dict:
        """
        Bootstrap the application with licensing enforcement.
        
        Returns:
            Dictionary with bootstrap results
        """
        logger.info("Starting application bootstrap")
        
        # 1. Initialize licensing (already done in __init__)
        
        # 2. Discover and filter features
        allowed_features, blocked_features = self.discover_and_filter_features()
        
        # 3. Load app config
        app_config = self.configurator.get_app_config()
        
        # 4. Return results
        return {
            "allowed_features": allowed_features,
            "blocked_features": blocked_features,
            "app_config": app_config,
            "licensing_active": self.licensing_service is not None,
            "license_valid": (
                self.licensing_service.get_verification().is_valid()
                if self.licensing_service
                else False
            )
        }


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Bootstrap application
    bootstrap = ApplicationBootstrap(project_root=".")
    results = bootstrap.bootstrap()
    
    print("\n=== Application Bootstrap Results ===")
    print(f"Licensing Active: {results['licensing_active']}")
    print(f"License Valid: {results['license_valid']}")
    print(f"\nAllowed Features ({len(results['allowed_features'])}):")
    for feature in results['allowed_features']:
        print(f"  - {feature.id}: {feature.label}")
    
    if results['blocked_features']:
        print(f"\nBlocked Features ({len(results['blocked_features'])}):")
        for feature in results['blocked_features']:
            print(f"  - {feature.id}: {feature.label}")
