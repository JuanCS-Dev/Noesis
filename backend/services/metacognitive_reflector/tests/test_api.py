"""
Unit tests for Metacognitive Reflector API routes.
"""

from __future__ import annotations


from fastapi import FastAPI
from fastapi.testclient import TestClient

from metacognitive_reflector.api.routes import router  # pylint: disable=import-error


# Create test app with router
app = FastAPI()
app.include_router(router, prefix="/v1")

client = TestClient(app)


def test_health_check():
    """Test health endpoint."""
    response = client.get("/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    assert response.json()["service"] == "metacognitive-reflector"
