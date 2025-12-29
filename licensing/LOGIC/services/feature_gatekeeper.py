"""
Feature Gatekeeper - Feature registration gatekeeper.

Author: QMToolV6 Development Team
Version: 1.0.0
"""

import logging
import re
from typing import Dict, Any

from licensing.MODELS.dto.entitlements_dto import EntitlementsDTO
from licensing.MODELS.dto.gate_decision_dto import GateDecisionDTO
from licensing.MODELS.enums.license_error_code import LicenseErrorCode
from licensing.LOGIC.interfaces.feature_gatekeeper_interface import FeatureGatekeeperInterface

logger = logging.getLogger(__name__)


class FeatureGatekeeper(FeatureGatekeeperInterface):
    """
    Feature gatekeeper implementation.
    
    Determines whether features should be registered based on their
    meta.json and current license entitlements.
    """
    
    FEATURE_CODE_PATTERN = re.compile(r'^[a-z0-9_]+$')
    
    def check_feature(
        self,
        meta: Dict[str, Any],
        entitlements: EntitlementsDTO
    ) -> GateDecisionDTO:
        """
        Check if feature should be allowed to register.
        
        Args:
            meta: Feature metadata from meta.json
            entitlements: Current license entitlements
            
        Returns:
            GateDecisionDTO with decision and reason
        """
        # 1. Check if feature is core (always allowed)
        if meta.get("is_core", False):
            logger.debug(f"Feature {meta.get('id')} is core, allowing registration")
            return GateDecisionDTO(
                allowed=True,
                feature_code=meta.get("id", "unknown"),
                reason="Core feature is always allowed",
                error_code=None
            )
        
        # 2. Check if feature requires license
        licensing_config = meta.get("licensing", {})
        requires_license = licensing_config.get("requires_license", False)
        
        if not requires_license:
            # Feature doesn't require license, allow
            logger.debug(f"Feature {meta.get('id')} doesn't require license")
            return GateDecisionDTO(
                allowed=True,
                feature_code=meta.get("id", "unknown"),
                reason="Feature does not require license",
                error_code=None
            )
        
        # 3. Validate feature_code
        feature_code = licensing_config.get("feature_code", "")
        if not feature_code:
            logger.error(f"Feature {meta.get('id')} requires license but has no feature_code")
            return GateDecisionDTO(
                allowed=False,
                feature_code=meta.get("id", "unknown"),
                reason="Feature requires license but feature_code is missing",
                error_code=LicenseErrorCode.FEATURE_META_INVALID
            )
        
        if not self.FEATURE_CODE_PATTERN.match(feature_code):
            logger.error(f"Invalid feature_code format: {feature_code}")
            return GateDecisionDTO(
                allowed=False,
                feature_code=feature_code,
                reason=f"Invalid feature_code format: {feature_code}",
                error_code=LicenseErrorCode.FEATURE_META_INVALID
            )
        
        # 4. Check entitlement
        if entitlements.is_entitled(feature_code):
            logger.info(f"Feature {feature_code} is entitled, allowing registration")
            return GateDecisionDTO(
                allowed=True,
                feature_code=feature_code,
                reason=f"Feature {feature_code} is entitled in license",
                error_code=None
            )
        else:
            logger.warning(f"Feature {feature_code} is not entitled, blocking registration")
            return GateDecisionDTO(
                allowed=False,
                feature_code=feature_code,
                reason=f"Feature {feature_code} is not entitled in license",
                error_code=LicenseErrorCode.FEATURE_NOT_ENTITLED
            )
