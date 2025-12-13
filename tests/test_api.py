"""Tests for the FastAPI server and authentication."""

import pytest
from fastapi.testclient import TestClient
from src.api import app
from src.config import settings


@pytest.fixture
def client(test_env):
    """Create a test client for the FastAPI app."""
    return TestClient(app)


def test_health_check(client):
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_valid_quiz_request(client, sample_quiz_url):
    """Test that a valid request returns 200."""
    payload = {
        "email": "test@example.com",
        "secret": "test-secret-123",
        "url": sample_quiz_url
    }
    
    response = client.post("/quiz", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "accepted"
    assert "message" in data


def test_invalid_secret(client, sample_quiz_url):
    """Test that an invalid secret returns 403."""
    payload = {
        "email": "test@example.com",
        "secret": "wrong-secret",
        "url": sample_quiz_url
    }
    
    response = client.post("/quiz", json=payload)
    
    assert response.status_code == 403
    assert "error" in response.json()


def test_invalid_json(client):
    """Test that invalid JSON returns 400."""
    response = client.post(
        "/quiz",
        data="not valid json",
        headers={"Content-Type": "application/json"}
    )
    
    assert response.status_code == 400
    assert "error" in response.json()


def test_missing_required_fields(client):
    """Test that missing required fields returns 400."""
    payload = {
        "email": "test@example.com"
        # Missing secret and url
    }
    
    response = client.post("/quiz", json=payload)
    
    assert response.status_code == 400
    assert "error" in response.json()


def test_invalid_email_format(client, sample_quiz_url):
    """Test that invalid email format returns 400."""
    payload = {
        "email": "not-an-email",
        "secret": "test-secret-123",
        "url": sample_quiz_url
    }
    
    response = client.post("/quiz", json=payload)
    
    assert response.status_code == 400
    assert "error" in response.json()


def test_invalid_url_format(client):
    """Test that invalid URL format returns 400."""
    payload = {
        "email": "test@example.com",
        "secret": "test-secret-123",
        "url": "not-a-valid-url"
    }
    
    response = client.post("/quiz", json=payload)
    
    assert response.status_code == 400
    assert "error" in response.json()


def test_empty_secret(client, sample_quiz_url):
    """Test that empty secret returns 400."""
    payload = {
        "email": "test@example.com",
        "secret": "",
        "url": sample_quiz_url
    }
    
    response = client.post("/quiz", json=payload)
    
    assert response.status_code == 400
    assert "error" in response.json()


def test_whitespace_only_secret(client, sample_quiz_url):
    """Test that whitespace-only secret returns 400."""
    payload = {
        "email": "test@example.com",
        "secret": "   ",
        "url": sample_quiz_url
    }
    
    response = client.post("/quiz", json=payload)
    
    assert response.status_code == 400
    assert "error" in response.json()
