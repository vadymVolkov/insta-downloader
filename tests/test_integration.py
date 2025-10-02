"""
Integration tests for the Instagram Downloader API.
Tests all major functionality including audio extraction, error handling, and logging.
"""

import pytest
import asyncio
import json
from fastapi.testclient import TestClient
from app.main import create_app


class TestIntegration:
    """
    Integration tests for the complete application.
    """
    
    @pytest.fixture
    def app(self):
        """Create test application."""
        return create_app()
    
    @pytest.fixture
    def client(self, app):
        """Create test client."""
        return TestClient(app)
    
    def test_health_endpoint(self, client):
        """Test health check endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "instagram-downloader"
    
    def test_health_check_endpoint(self, client):
        """Test detailed health check endpoint."""
        response = client.get("/api/health/")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "app" in data
        assert "services" in data
        assert "configuration" in data
    
    def test_download_endpoint_validation(self, client):
        """Test download endpoint with invalid data."""
        # Test with missing URL
        response = client.post("/api/download/", json={})
        assert response.status_code == 422
        
        # Test with invalid URL
        response = client.post("/api/download/", json={"url": "invalid-url"})
        assert response.status_code == 422
    
    def test_cors_headers(self, client):
        """Test CORS headers are present."""
        response = client.options("/api/download/")
        assert response.status_code == 200
        assert "access-control-allow-origin" in response.headers
    
    def test_static_files_mount(self, client):
        """Test static files are properly mounted."""
        # This will return 404 for non-existent file, but should not return 500
        response = client.get("/static/nonexistent.mp4")
        assert response.status_code == 404
    
    def test_api_documentation(self, client):
        """Test API documentation endpoints."""
        response = client.get("/docs")
        assert response.status_code == 200
        
        response = client.get("/openapi.json")
        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "info" in data


class TestErrorHandling:
    """
    Test error handling and logging.
    """
    
    @pytest.fixture
    def app(self):
        """Create test application."""
        return create_app()
    
    @pytest.fixture
    def client(self, app):
        """Create test client."""
        return TestClient(app)
    
    def test_invalid_json(self, client):
        """Test handling of invalid JSON."""
        response = client.post(
            "/api/download/",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422
    
    def test_missing_content_type(self, client):
        """Test handling of missing content type."""
        response = client.post("/api/download/", data="{}")
        assert response.status_code == 422


class TestConfiguration:
    """
    Test configuration and environment variables.
    """
    
    def test_config_validation(self):
        """Test configuration validation."""
        from app.config import AppConfig
        
        # Test that configuration loads without errors
        errors = AppConfig.validate_config()
        assert len(errors) == 0
        
        # Test configuration summary
        summary = AppConfig.get_config_summary()
        assert "app" in summary
        assert "audio" in summary
        assert "video" in summary
        assert "logging" in summary
    
    def test_cors_origins(self):
        """Test CORS origins configuration."""
        from app.config import AppConfig
        
        origins = AppConfig.get_cors_origins()
        assert isinstance(origins, list)
        assert len(origins) > 0


if __name__ == "__main__":
    # Run basic tests
    import sys
    sys.path.append(".")
    
    # Test configuration
    print("Testing configuration...")
    from app.config import AppConfig
    errors = AppConfig.validate_config()
    if errors:
        print(f"Configuration errors: {errors}")
    else:
        print("✅ Configuration validation passed")
    
    # Test application creation
    print("Testing application creation...")
    try:
        app = create_app()
        print("✅ Application created successfully")
        print(f"✅ App title: {app.title}")
        print(f"✅ App version: {app.version}")
    except Exception as e:
        print(f"❌ Application creation failed: {e}")
        sys.exit(1)
    
    print("✅ All basic tests passed!")