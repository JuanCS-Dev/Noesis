"""
Unit tests for API Gateway Routes.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
from backend.services.api_gateway.api.routes import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

@pytest.mark.asyncio
async def test_gateway_proxy_route():
    with patch("backend.services.api_gateway.core.proxy.ServiceProxy.forward_request") as mock_forward:
        mock_forward.return_value = {"status": "forwarded"}
        
        response = client.get("/meta_orchestrator/health")
        
        assert response.status_code == 200
        assert response.json() == {"status": "forwarded"}
        mock_forward.assert_called_once()
