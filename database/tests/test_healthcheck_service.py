"""Tests for HealthcheckService."""
import pytest

from database.logic.services.healthcheck_service import HealthcheckService, HealthCheckResult


class TestHealthcheckService:
    """Tests for HealthcheckService."""
    
    @pytest.fixture
    def healthcheck_service(self, database_service):
        """Create healthcheck service."""
        return HealthcheckService(database_service)
    
    def test_initialization(self, healthcheck_service):
        """Test healthcheck service initialization."""
        # Assert
        assert healthcheck_service is not None
    
    def test_check_health(self, healthcheck_service):
        """Test health check."""
        # Act
        result = healthcheck_service.check_health()
        
        # Assert
        assert isinstance(result, HealthCheckResult)
        assert result.is_healthy is True
        assert result.response_time_ms > 0
        assert result.error_message is None
    
    def test_ping(self, healthcheck_service):
        """Test ping."""
        # Act
        result = healthcheck_service.ping()
        
        # Assert
        assert result is True
    
    def test_get_connection_info(self, healthcheck_service):
        """Test getting connection info."""
        # Act
        info = healthcheck_service.get_connection_info()
        
        # Assert
        assert isinstance(info, dict)
        assert "database_url" in info
        assert "engine_name" in info
        assert "is_connected" in info
        assert info["is_connected"] is True
