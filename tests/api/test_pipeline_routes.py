import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from api.main import app

# We won't use AsyncClient here just to do a simple sync TestClient check
client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "version": "0.1.0"}

@patch("api.routes.memory.get_memory")
def test_read_artifact_not_found(mock_get_memory):
    # Mock the singleton
    mock_memory = MagicMock()
    mock_memory.read_artifact.return_value = {"exists": False}
    mock_get_memory.return_value = mock_memory
    
    response = client.get("/memory/artifact/week_1/01_research/missing.md")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()

@patch("api.routes.memory.get_memory")
def test_read_artifact_success(mock_get_memory):
    mock_memory = MagicMock()
    mock_memory.read_artifact.return_value = {
        "exists": True,
        "content": "# Hello",
        "metadata": {"author": "system"}
    }
    mock_get_memory.return_value = mock_memory
    
    response = client.get("/memory/artifact/week_1/01_research/found.md")
    assert response.status_code == 200
    data = response.json()
    assert data["content"] == "# Hello"
    assert data["metadata"]["author"] == "system"
