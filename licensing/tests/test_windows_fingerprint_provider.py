"""
Tests for Windows fingerprint provider.

Author: QMToolV6 Development Team
Version: 1.0.0
"""

import pytest

from licensing.LOGIC.fingerprint.windows_fingerprint_provider import WindowsFingerprintProvider


class TestWindowsFingerprintProvider:
    """Test WindowsFingerprintProvider."""
    
    @pytest.fixture
    def provider(self):
        """Create fingerprint provider instance."""
        return WindowsFingerprintProvider()
    
    def test_get_fingerprint_returns_dto(self, provider):
        """Test that get_fingerprint returns a valid DTO."""
        fp = provider.get_fingerprint()
        
        assert fp is not None
        assert fp.canonical_string is not None
        assert fp.hash is not None
        assert fp.hash.startswith("hex:")
    
    def test_get_fingerprint_hash_returns_hash(self, provider):
        """Test that get_fingerprint_hash returns a hash string."""
        hash_str = provider.get_fingerprint_hash()
        
        assert hash_str is not None
        assert hash_str.startswith("hex:")
        assert len(hash_str) > 4  # More than just "hex:"
    
    def test_canonical_string_format(self, provider):
        """Test that canonical string has correct format."""
        fp = provider.get_fingerprint()
        
        assert "MG=" in fp.canonical_string
        assert "UUID=" in fp.canonical_string
        assert "MB=" in fp.canonical_string
        assert fp.canonical_string.count("|") == 2
    
    def test_fingerprint_is_consistent(self, provider):
        """Test that fingerprint is consistent across calls."""
        fp1 = provider.get_fingerprint()
        fp2 = provider.get_fingerprint()
        
        assert fp1.hash == fp2.hash
        assert fp1.canonical_string == fp2.canonical_string
