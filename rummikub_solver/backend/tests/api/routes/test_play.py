"""Quick-play route tests."""

import pytest
from fastapi.testclient import TestClient
from src.main import app

from src.core.redis import get_redis

class MockRedis:
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

@pytest.fixture(autouse=True)
def setup_dependency_overrides():
    app.dependency_overrides[get_redis] = override_get_redis
    yield
    app.dependency_overrides.clear()

client = TestClient(app)

def test_next_play_completed(mocker):
    mocker.patch("src.api.routes.play.get_play_by_id", return_value={"sets": []})
    login_response = client.post("/login", json={"email": "gamer@example.com", "password": "Passw0rd!"})
    token = login_response.json()["access_token"]
    response = client.get("/next-play/49701ce8-c174-4b53-855f-ef717f001ccd", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["status"] == "completed"

def test_next_play_processing(mocker):
    from src.core.exceptions import PlayProcessingError
    mocker.patch("src.api.routes.play.get_play_by_id", side_effect=PlayProcessingError())
    login_response = client.post("/login", json={"email": "gamer@example.com", "password": "Passw0rd!"})
    token = login_response.json()["access_token"]
    response = client.get("/next-play/49701ce8-c174-4b53-855f-ef717f001ccd", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 202
    assert response.json()["detail"] == "Play is still processing"

def test_next_play_failed(mocker):
    from src.core.exceptions import PlayFailedError
    mocker.patch("src.api.routes.play.get_play_by_id", side_effect=PlayFailedError(failure_code="ERR", failure_message="Failed"))
    login_response = client.post("/login", json={"email": "gamer@example.com", "password": "Passw0rd!"})
    token = login_response.json()["access_token"]
    response = client.get("/next-play/49701ce8-c174-4b53-855f-ef717f001ccd", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "ERR"

def test_next_play_not_found(mocker):
    from src.core.exceptions import PlayNotFoundError
    mocker.patch("src.api.routes.play.get_play_by_id", side_effect=PlayNotFoundError())
    login_response = client.post("/login", json={"email": "gamer@example.com", "password": "Passw0rd!"})
    token = login_response.json()["access_token"]
    response = client.get("/next-play/49701ce8-c174-4b53-855f-ef717f001ccd", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 404
