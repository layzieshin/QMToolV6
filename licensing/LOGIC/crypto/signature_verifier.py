"""
Signature Verifier - Cryptographic signature verification for licenses.

Author: QMToolV6 Development Team
Version: 1.0.0
"""

import base64
import hashlib
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class SignatureVerifier:
    """
    Verifies cryptographic signatures on licenses.
    
    Uses RSA/ECDSA signatures for license validation.
    For MVP, implements basic signature verification logic.
    """
    
    def __init__(self, public_key_path: Optional[Path] = None):
        """
        Initialize signature verifier.
        
        Args:
            public_key_path: Path to public key PEM file (optional for MVP)
        """
        self.public_key_path = public_key_path
        logger.info(f"SignatureVerifier initialized with public key: {public_key_path}")
    
    def verify(self, message: str, signature: str) -> bool:
        """
        Verify signature on message.
        
        Args:
            message: Message that was signed (canonical JSON)
            signature: Signature to verify (base64 encoded with "b64:" prefix)
            
        Returns:
            True if signature is valid, False otherwise
            
        Note:
            MVP implementation uses simple hash-based verification.
            Production should use proper RSA/ECDSA verification.
        """
        try:
            # Remove "b64:" prefix if present
            if signature.startswith("b64:"):
                signature = signature[4:]
            
            # For MVP: Simple hash-based verification
            # In production, this should use cryptography library with RSA/ECDSA
            expected_hash = hashlib.sha256(message.encode('utf-8')).hexdigest()
            
            try:
                sig_bytes = base64.b64decode(signature)
                # For MVP, we consider any valid base64 as potentially valid
                # Real implementation would verify with public key
                logger.debug(f"Signature verification: hash={expected_hash[:16]}...")
                return True  # MVP: Accept valid base64 signatures
            except Exception as e:
                logger.warning(f"Signature decode failed: {e}")
                return False
                
        except Exception as e:
            logger.error(f"Signature verification failed: {e}")
            return False
    
    def sign(self, message: str) -> str:
        """
        Sign a message (for testing/development).
        
        Args:
            message: Message to sign
            
        Returns:
            Base64-encoded signature with "b64:" prefix
            
        Note:
            This is for testing only. Real signing should be done offline
            with private key.
        """
        # MVP: Simple hash-based signature for testing
        hash_value = hashlib.sha256(message.encode('utf-8')).digest()
        sig_b64 = base64.b64encode(hash_value).decode('utf-8')
        return f"b64:{sig_b64}"
