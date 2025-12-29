"""
Entitlements DTO - Feature entitlements from license.

Author: QMToolV6 Development Team
Version: 1.0.0
"""

from dataclasses import dataclass, field
from typing import Dict


@dataclass(frozen=True)
class EntitlementsDTO:
    """
    Feature entitlements DTO.
    
    Represents which features are enabled/licensed.
    
    Attributes:
        features: Mapping of feature_code to entitlement status
    
    Example:
        >>> entitlements = EntitlementsDTO(
        ...     features={"translation": True, "documentlifecycle": True}
        ... )
        >>> entitlements.is_entitled("translation")
        True
        >>> entitlements.is_entitled("unknown")
        False
    """
    
    features: Dict[str, bool] = field(default_factory=dict)
    """Feature entitlements mapping (feature_code -> bool)."""
    
    def is_entitled(self, feature_code: str) -> bool:
        """
        Check if a feature is entitled.
        
        Args:
            feature_code: Feature code to check
            
        Returns:
            True if feature is entitled, False otherwise
        """
        return self.features.get(feature_code, False)
    
    def get_entitled_features(self) -> list[str]:
        """
        Get list of entitled features.
        
        Returns:
            List of feature codes that are entitled
        """
        return [code for code, entitled in self.features.items() if entitled]
