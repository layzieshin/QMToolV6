"""
Loader exceptions.

Author: QMToolV6 Development Team
Version: 1.0.0
"""


class BootstrapError(Exception):
    """Base exception for bootstrap errors."""
    pass


class AuditSinkNotAvailableError(BootstrapError):
    """
    Raised when audit sink is not available.
    
    According to policies, audittrail is mandatory and must be
    registered before any audit-required features can boot.
    This is a hard failure - the application cannot start without audit.
    """
    
    def __init__(self, message: str = "Audit sink is not available. Audit is mandatory."):
        super().__init__(message)


class FeatureLoadError(BootstrapError):
    """Raised when a feature fails to load."""
    
    def __init__(self, feature_id: str, reason: str):
        self.feature_id = feature_id
        self.reason = reason
        super().__init__(f"Failed to load feature '{feature_id}': {reason}")


class DependencyError(BootstrapError):
    """Raised when a dependency cannot be resolved."""
    
    def __init__(self, feature_id: str, dependency: str):
        self.feature_id = feature_id
        self.dependency = dependency
        super().__init__(f"Feature '{feature_id}' depends on '{dependency}' which is not available")


class CyclicDependencyError(BootstrapError):
    """Raised when a cyclic dependency is detected in feature graph."""
    
    def __init__(self, cycle: list):
        self.cycle = cycle
        super().__init__(f"Cyclic dependency detected: {' -> '.join(cycle)}")
