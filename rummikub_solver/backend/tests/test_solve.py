"""Solver endpoint tests."""

import pytest
from fastapi.testclient import TestClient
from uuid import uuid4
from src.main import app
from src.core.redis import get_redis
from src.core.database import get_db

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
    async def delete(self, key: str) -> int:
        if key in self.data:
            del self.data[key]
            return 1
        return 0
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

def get_auth_headers(user_id="gamer", email="gamer@example.com"):
    login_response = client.post("/login", json={"email": f"{user_id}@example.com", "password": "Passw0rd!"})
    token = login_response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

class MockBoard:
    def __init__(self, id, user_id, status="completed", solution=None):
        self.id = id
        self.user_id = user_id
        self.status = status
        self.solution = solution
        self.classification_results = None
        self.fix_results = None
        self.hand_results = None

def test_trigger_solve_board_success(mocker):
    board_id = "49701ce8-c174-4b53-855f-ef717f001ccd"
    board = MockBoard(id=board_id, user_id="mock-user-gamer", status="completed")
    
    mock_db = mocker.Mock()
    mock_db.execute = mocker.AsyncMock()
    mock_db.flush = mocker.AsyncMock()
    mock_db.commit = mocker.AsyncMock()
    mocker.patch("src.services.board_service.get_board_by_id", return_value=board)
    mocker.patch("src.services.play_service.celery_app.send_task")
    app.dependency_overrides[get_db] = lambda: mock_db
    
    headers = get_auth_headers(user_id="gamer")
    
    response = client.post(f"/next-play/{board_id}/solve", headers=headers)
    assert response.status_code == 202
    assert response.json()["message"] == "Solver task dispatched"
    assert board.solution == {}
    
    # attempt correction
    # Need to update routes/play.py get_board_by_id mock if testing correct
    mocker.patch("src.api.routes.play.get_board_by_id", return_value=board)
    payload = {"sets": [], "unassigned": [], "hand": []}
    correct_response = client.post(f"/correct/{board_id}", json=payload, headers=headers)
    assert correct_response.status_code == 400
    assert "locked for solving" in correct_response.json()["detail"]


def test_trigger_solve_board_not_found(mocker):
    board_id = "49701ce8-c174-4b53-855f-ef717f001ccd"
    
    mock_db = mocker.Mock()
    mocker.patch("src.services.board_service.get_board_by_id", return_value=None)
    app.dependency_overrides[get_db] = lambda: mock_db
    
    headers = get_auth_headers(user_id="gamer")
    
    response = client.post(f"/api/v1/play/next-play/{board_id}/solve", headers=headers)
    assert response.status_code == 404


def test_trigger_solve_board_wrong_status(mocker):
    board_id = "49701ce8-c174-4b53-855f-ef717f001ccd"
    board = MockBoard(id=board_id, user_id="mock-user-gamer", status="processing")
    
    mock_db = mocker.Mock()
    mocker.patch("src.services.board_service.get_board_by_id", return_value=board)
    app.dependency_overrides[get_db] = lambda: mock_db
    
    headers = get_auth_headers(user_id="gamer")
    
    response = client.post(f"/next-play/{board_id}/solve", headers=headers)
    assert response.status_code == 400
    assert "not completed" in response.json()["detail"]
