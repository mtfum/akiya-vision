"""
API tests for AkiyaVision
"""
import pytest
from fastapi.testclient import TestClient
import json


def test_server_starts(client):
    """Test that the server starts and root endpoint works"""
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_get_houses(client):
    """Test /api/houses endpoint returns correct data"""
    response = client.get("/api/houses")
    assert response.status_code == 200
    
    houses = response.json()
    assert len(houses) == 2
    
    # Check first house
    house1 = houses[0]
    assert house1["id"] == "house1"
    assert house1["name"] == "世田谷区 - 古民家"
    assert house1["price"] == "3,800万円"
    assert house1["area"] == "180㎡"
    assert house1["age"] == "築80年"
    
    # Check second house
    house2 = houses[1]
    assert house2["id"] == "house2"
    assert house2["name"] == "杉並区 - 一戸建て"
    assert house2["price"] == "5,200万円"


def test_upload_image_invalid_house(client):
    """Test upload to non-existent house returns 404"""
    response = client.post(
        "/api/upload/invalid_house_id",
        files={"file": ("test.jpg", b"fake image data", "image/jpeg")}
    )
    assert response.status_code == 404
    assert "House not found" in response.json()["detail"]


def test_upload_image_invalid_file_type(client):
    """Test upload of non-allowed file type returns 400"""
    response = client.post(
        "/api/upload/house1",
        files={"file": ("test.txt", b"not an allowed file", "text/plain")}
    )
    assert response.status_code == 400
    assert "ファイルタイプが無効です" in response.json()["detail"]


def test_upload_image_success(client, sample_image_base64):
    """Test successful image upload"""
    import base64
    image_data = base64.b64decode(sample_image_base64)
    
    response = client.post(
        "/api/upload/house1",
        files={"file": ("test.png", image_data, "image/png")}
    )
    assert response.status_code == 200
    
    result = response.json()
    assert "image_id" in result
    assert result["message"] == "Image uploaded successfully"
    
    # Verify image was added to house
    houses_response = client.get("/api/houses")
    houses = houses_response.json()
    house1 = next(h for h in houses if h["id"] == "house1")
    assert len(house1["images"]) == 1
    assert house1["images"][0]["id"] == result["image_id"]


def test_renovate_image_invalid_house(client):
    """Test renovate with invalid house ID returns 404"""
    response = client.post(
        "/api/renovate/invalid_house/some_image",
        json={"style": "modern"}
    )
    assert response.status_code == 404
    assert "House not found" in response.json()["detail"]


def test_renovate_image_invalid_style(client, sample_image_base64):
    """Test renovate with invalid style returns 400"""
    # First upload an image
    import base64
    image_data = base64.b64decode(sample_image_base64)
    
    upload_response = client.post(
        "/api/upload/house1",
        files={"file": ("test.png", image_data, "image/png")}
    )
    image_id = upload_response.json()["image_id"]
    
    # Try to renovate with invalid style
    response = client.post(
        f"/api/renovate/house1/{image_id}",
        json={"style": "invalid_style"}
    )
    assert response.status_code == 400
    assert "Invalid style" in response.json()["detail"]


def test_renovate_image_mock_response(client, sample_image_base64):
    """Test renovate returns mock response when no API key"""
    # First upload an image
    import base64
    image_data = base64.b64decode(sample_image_base64)
    
    upload_response = client.post(
        "/api/upload/house1",
        files={"file": ("test.png", image_data, "image/png")}
    )
    image_id = upload_response.json()["image_id"]
    
    # Test each style
    for style in ["modern", "traditional", "western", "scandinavian"]:
        response = client.post(
            f"/api/renovate/house1/{image_id}",
            json={"style": style}
        )
        assert response.status_code == 200
        
        result = response.json()
        assert result["status"] == "succeeded"
        assert result["style"] == style
        assert "Mock response" in result["message"]
        assert len(result["output"]) == 1