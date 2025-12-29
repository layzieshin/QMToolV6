"""
Feature Gatekeeper Interface.

Author: QMToolV6 Development Team
Version: 1.0.0
"""

from abc import ABC, abstractmethod
from typing import Dict, Any

from licensing.MODELS.dto.entitlements_dto import EntitlementsDTO
from licensing.MODELS.dto.gate_decision_dto import GateDecisionDTO


class FeatureGatekeeperInterface(ABC):
    """
    Interface for feature gatekeeper.
    
    Determines whether features should be allowed to register based on
    their meta.json and current license entitlements.
    """
    
    @abstractmethod
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
        pass
