"""
Test configuration and fixtures for AkiyaVision tests.
"""
import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    from app import app
    return TestClient(app)


@pytest.fixture
def sample_image_base64():
    """Provide a small base64 encoded test image."""
    # 1x1 pixel transparent PNG
    return "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="


@pytest.fixture
def mock_replicate_response():
    """Mock response from Replicate API."""
    return {
        "id": "test-prediction-id",
        "status": "succeeded",
        "output": ["https://replicate.delivery/pbxt/test-image.png"]
    }