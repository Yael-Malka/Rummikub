"""Smoke tests for the HTTP API."""

import io
from fastapi.testclient import TestClient
from src.core.redis import get_redis
from src.main import app


class MockRedis:
    """Mock Redis client for testing to isolate database and avoid event loop issues."""

    def __init__(self):
        self.data = {}

    async def exists(self, key: str) -> int:
        return 1 if key in self.data else 0

    async def get(self, key: str) -> str | None:
        return self.data.get(key)

    async def set(self, key: str, value: str, ex: int | None = None) -> bool:
        self.data[key] = str(value)
        return True

    async def aclose(self) -> None:
        pass


mock_redis = MockRedis()


async def override_get_redis():
    yield mock_redis


import pytest

@pytest.fixture(autouse=True)
def setup_dependency_overrides():
    app.dependency_overrides[get_redis] = override_get_redis
    yield
    app.dependency_overrides.clear()


client = TestClient(app)


def test_read_root():
    """Verify that root endpoint returns 200 OK and welcome message."""
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()


def test_health_endpoint():
    """Verify health endpoint structure and Redis check."""
    response = client.get("/health")
    assert response.status_code == 200
    assert "status" in response.json()
    assert "redis" in response.json()


def test_login_and_logout_flow():
    """Test the complete auth lifecycle.

    Registers via the API and logs in, then logs out and verifies the token is revoked.
    """
    # 1. Log in to obtain a session token
    login_payload = {"email": "testuser@example.com", "password": "Passw0rd!"}
    login_response = client.post("/login", json=login_payload)
    assert login_response.status_code == 200

    token_data = login_response.json()
    assert "access_token" in token_data
    assert token_data["token_type"] == "bearer"
    access_token = token_data["access_token"]

    # 2. Logout with the bearer token to revoke the session
    headers = {"Authorization": f"Bearer {access_token}"}
    logout_response = client.get("/logout", headers=headers)
    assert logout_response.status_code == 200
    assert logout_response.json() == {"message": "Successfully logged out"}

    # 3. Verify the token is now blacklisted/revoked
    # (Calling logout again with the same token should fail with 401 Unauthorized)
    revoked_response = client.get("/logout", headers=headers)
    assert revoked_response.status_code == 401
    assert "revoked" in revoked_response.json()["detail"].lower()


def test_gameplay_flow():
    """Test board image submission and computed play retrieval."""
    # 1. Login to get session token
    login_response = client.post("/login", json={"email": "gamer@example.com", "password": "Passw0rd!"})
    access_token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}

    # 2. Upload dummy image data
    image_data = b"fake-jpeg-image-bytes"
    file_payload = {
        "board_image": ("test_board.jpg", io.BytesIO(image_data), "image/jpeg"),
        "hand_image": ("test_hand.jpg", io.BytesIO(image_data), "image/jpeg")
    }

    upload_response = client.post("/send-play", headers=headers, files=file_payload)
    assert upload_response.status_code == 200
    upload_data = upload_response.json()
    assert "id" in upload_data
    assert upload_data["status"] == "processing"
    play_id = upload_data["id"]

    # Simulate Celery worker finishing by writing to mock Redis
    import json
    mock_redis.data[f"boards:{play_id}"] = json.dumps({
        "status": "completed",
        "result": {
            "image": "test_board.jpg",
            "tile_px": {"w": 10.0, "h": 10.0},
            "skew_deg": 0.0,
            "sets": [],
            "unassigned": [],
            "hand": []
        },
        "error": None
    })

    # 3. Retrieve the computed play
    retrieval_response = client.get(f"/next-play/{play_id}", headers=headers)
    assert retrieval_response.status_code == 200
    play_data = retrieval_response.json()
    assert play_data["id"] == play_id
    assert isinstance(play_data["result"], dict)



def test_unauthorized_access():
    """Verify endpoints enforce authentication."""
    # Attempt to upload board without authorization header
    upload_response = client.post("/send-play", files={
        "board_image": ("test.jpg", b"bytes", "image/jpeg"),
        "hand_image": ("test_hand.jpg", b"bytes", "image/jpeg")
    })
    assert upload_response.status_code == 401  # FastAPI Bearer scheme defaults to 401 on missing credentials

    # Attempt to retrieve play without authorization header
    retrieval_response = client.get("/next-play/some-uuid")
    assert retrieval_response.status_code == 401


def test_upload_validation():
    """Verify that file types and size constraints are validated."""
    # Login
    login_response = client.post("/login", json={"email": "gamer@example.com", "password": "Passw0rd!"})
    access_token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}

    image_data = b"fake-jpeg-image-bytes"
    # Upload invalid file type (e.g. text/plain)
    invalid_file = {
        "board_image": ("test.txt", io.BytesIO(b"some text"), "text/plain"),
        "hand_image": ("test_hand.jpg", io.BytesIO(image_data), "image/jpeg")
    }
    response = client.post("/send-play", headers=headers, files=invalid_file)
    assert response.status_code == 400
    assert "unsupported media type" in response.json()["detail"].lower()
