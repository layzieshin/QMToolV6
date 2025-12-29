"""
Machine Fingerprint Provider Interface.

Author: QMToolV6 Development Team
Version: 1.0.0
"""

from abc import ABC, abstractmethod

from licensing.MODELS.dto.machine_fingerprint_dto import MachineFingerprintDTO


class MachineFingerprintProviderInterface(ABC):
    """
    Interface for machine fingerprint providers.
    
    Implementations provide hardware-based machine fingerprinting.
    """
    
    @abstractmethod
    def get_fingerprint(self) -> MachineFingerprintDTO:
        """
        Get machine fingerprint with all components.
        
        Returns:
            MachineFingerprintDTO with fingerprint data
            
        Raises:
            RuntimeError: If unable to retrieve fingerprint
        """
        pass
    
    @abstractmethod
    def get_fingerprint_hash(self) -> str:
        """
        Get only the fingerprint hash.
        
        Returns:
            Fingerprint hash (hex:<sha256>)
            
        Raises:
            RuntimeError: If unable to retrieve fingerprint
        """
        pass
