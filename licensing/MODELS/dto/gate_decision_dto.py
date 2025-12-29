"""
Gate Decision DTO - Feature gatekeeper decision.

Author: QMToolV6 Development Team
Version: 1.0.0
"""

from dataclasses import dataclass
from typing import Optional

from licensing.MODELS.enums.license_error_code import LicenseErrorCode


@dataclass(frozen=True)
class GateDecisionDTO:
    """
    Feature gatekeeper decision DTO.
    
    Result of checking whether a feature should be allowed to register.
    
    Attributes:
        allowed: Whether feature is allowed to register
        feature_code: Feature code being checked
        reason: Reason for decision
        error_code: Error code if not allowed
    
    Example:
        >>> decision = GateDecisionDTO(
        ...     allowed=True,
        ...     feature_code="translation",
        ...     reason="Feature is entitled in license",
        ...     error_code=None
        ... )
    """
    
    allowed: bool
    """Whether feature registration is allowed."""
    
    feature_code: str
    """Feature code being checked."""
    
    reason: str
    """Human-readable reason for decision."""
    
    error_code: Optional[LicenseErrorCode] = None
    """Error code if not allowed."""
