"""Board correction endpoint tests."""

import pytest
from fastapi.testclient import TestClient
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
    # Generate mock login token
    login_response = client.post("/login", json={"email": f"{user_id}@example.com", "password": "Passw0rd!"})
    token = login_response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


class MockBoard:
    def __init__(self, id, user_id, status="completed", classification_results=None, fix_results=None, hand_results=None, image_path="board.jpeg"):
        self.id = id
        self.user_id = user_id
        self.status = status
        self.classification_results = classification_results or {
            "image": "board.jpeg",
            "tile_px": {"w": 186.0, "h": 141.5},
            "skew_deg": 80.6,
            "sets": [],
            "unassigned": []
        }
        self.fix_results = fix_results
        self.hand_results = hand_results or []
        self.image_path = image_path
        self.failure_code = "SOME_ERROR" if status == "failed" else None
        self.failure_message = "Some error message" if status == "failed" else None


# T006: Integration and unit tests for the correction endpoint
def test_correct_completed_success(mocker):
    # Mock DB Board
    board_id = "49701ce8-c174-4b53-855f-ef717f001ccd"
    board = MockBoard(id=board_id, user_id="mock-user-gamer", status="completed")
    
    # Mock DB session and lookup
    mock_db = mocker.Mock()
    mock_db.execute = mocker.AsyncMock()
    mock_db.flush = mocker.AsyncMock()
    mock_db.commit = mocker.AsyncMock()
    mocker.patch("src.api.routes.play.get_board_by_id", return_value=board)
    mocker.patch("src.services.board_service.get_board_by_id", return_value=board)
    app.dependency_overrides[get_db] = lambda: mock_db
    
    # Setup mock Redis data
    mock_redis.data[f"boards:{board_id}"] = "completed" # simulate cached representation
    
    headers = get_auth_headers(user_id="gamer")
    
    payload = {
        "sets": [
            {
                "tiles": [
                    {"color": "blue", "number": "1"},
                    {"color": "blue", "number": "2"},
                    {"color": "blue", "number": "3"}
                ]
            }
        ],
        "unassigned": [],
        "hand": [
            {"color": "red", "number": "7"}
        ]
    }
    
    response = client.post(f"/correct/{board_id}", json=payload, headers=headers)
    assert response.status_code == 200
    
    res_data = response.json()
    assert res_data["status"] == "completed"
    assert res_data["result"]["sets"][0]["tiles"][0]["color"] == "blue"
    assert res_data["result"]["hand"][0]["color"] == "red"
    
    # Verify DB was modified appropriately (fix_results and hand_results updated, classification_results untouched)
    assert board.fix_results == {
        "sets": [
            {
                "tiles": [
                    {"color": "blue", "number": "1"},
                    {"color": "blue", "number": "2"},
                    {"color": "blue", "number": "3"}
                ]
            }
        ],
        "unassigned": []
    }
    assert board.hand_results == [{"color": "red", "number": "7"}]
    assert board.status == "completed"


def test_correct_failed_transitions_to_completed(mocker):
    board_id = "49701ce8-c174-4b53-855f-ef717f001ccd"
    board = MockBoard(id=board_id, user_id="mock-user-gamer", status="failed")
    
    mock_db = mocker.Mock()
    mock_db.execute = mocker.AsyncMock()
    mock_db.flush = mocker.AsyncMock()
    mock_db.commit = mocker.AsyncMock()
    mocker.patch("src.api.routes.play.get_board_by_id", return_value=board)
    mocker.patch("src.services.board_service.get_board_by_id", return_value=board)
    app.dependency_overrides[get_db] = lambda: mock_db
    
    headers = get_auth_headers(user_id="gamer")
    
    payload = {
        "sets": [
            {
                "tiles": [
                    {"color": "red", "number": "10"},
                    {"color": "blue", "number": "10"},
                    {"color": "black", "number": "10"}
                ]
            }
        ],
        "unassigned": [],
        "hand": []
    }
    
    response = client.post(f"/correct/{board_id}", json=payload, headers=headers)
    assert response.status_code == 200
    
    res_data = response.json()
    assert res_data["status"] == "completed"
    assert board.status == "completed"
    assert board.failure_code is None
    assert board.failure_message is None


def test_correct_processing_rejected(mocker):
    board_id = "49701ce8-c174-4b53-855f-ef717f001ccd"
    board = MockBoard(id=board_id, user_id="mock-user-gamer", status="processing")
    
    mock_db = mocker.Mock()
    mocker.patch("src.api.routes.play.get_board_by_id", return_value=board)
    app.dependency_overrides[get_db] = lambda: mock_db
    
    headers = get_auth_headers(user_id="gamer")
    
    payload = {
        "sets": [],
        "unassigned": [],
        "hand": []
    }
    
    response = client.post(f"/correct/{board_id}", json=payload, headers=headers)
    assert response.status_code == 400
    assert "processing" in response.json()["detail"].lower()


def test_correct_unauthorized_owner(mocker):
    board_id = "49701ce8-c174-4b53-855f-ef717f001ccd"
    board = MockBoard(id=board_id, user_id="mock-user-gamer-A", status="completed")
    
    mock_db = mocker.Mock()
    mocker.patch("src.api.routes.play.get_board_by_id", return_value=board)
    app.dependency_overrides[get_db] = lambda: mock_db
    
    headers = get_auth_headers(user_id="gamer-B")  # Different user
    
    payload = {
        "sets": [],
        "unassigned": [],
        "hand": []
    }
    
    response = client.post(f"/correct/{board_id}", json=payload, headers=headers)
    assert response.status_code == 403


def test_correct_not_found(mocker):
    board_id = "49701ce8-c174-4b53-855f-ef717f001ccd"
    
    mock_db = mocker.Mock()
    mocker.patch("src.api.routes.play.get_board_by_id", return_value=None)
    app.dependency_overrides[get_db] = lambda: mock_db
    
    headers = get_auth_headers(user_id="gamer")
    
    payload = {
        "sets": [],
        "unassigned": [],
        "hand": []
    }
    
    response = client.post(f"/correct/{board_id}", json=payload, headers=headers)
    assert response.status_code == 404


def test_correct_invalid_set_length(mocker):
    board_id = "49701ce8-c174-4b53-855f-ef717f001ccd"
    board = MockBoard(id=board_id, user_id="mock-user-gamer", status="completed")
    
    mock_db = mocker.Mock()
    mocker.patch("src.api.routes.play.get_board_by_id", return_value=board)
    app.dependency_overrides[get_db] = lambda: mock_db
    
    headers = get_auth_headers(user_id="gamer")
    
    # Set of length 2 is invalid
    payload = {
        "sets": [
            {
                "tiles": [
                    {"color": "blue", "number": "1"},
                    {"color": "blue", "number": "2"}
                ]
            }
        ],
        "unassigned": [],
        "hand": []
    }
    
    response = client.post(f"/correct/{board_id}", json=payload, headers=headers)
    assert response.status_code == 400
    assert "at least 3 tiles" in response.json()["detail"]


def test_correct_invalid_meld(mocker):
    board_id = "49701ce8-c174-4b53-855f-ef717f001ccd"
    board = MockBoard(id=board_id, user_id="mock-user-gamer", status="completed")
    
    mock_db = mocker.Mock()
    mocker.patch("src.api.routes.play.get_board_by_id", return_value=board)
    app.dependency_overrides[get_db] = lambda: mock_db
    
    headers = get_auth_headers(user_id="gamer")
    
    # 1-2-5 of blue is not a valid run
    payload = {
        "sets": [
            {
                "tiles": [
                    {"color": "blue", "number": "1"},
                    {"color": "blue", "number": "2"},
                    {"color": "blue", "number": "5"}
                ]
            }
        ],
        "unassigned": [],
        "hand": []
    }
    
    response = client.post(f"/correct/{board_id}", json=payload, headers=headers)
    assert response.status_code == 400
    assert "not a valid run or group" in response.json()["detail"]


def test_correct_non_empty_unassigned(mocker):
    board_id = "49701ce8-c174-4b53-855f-ef717f001ccd"
    board = MockBoard(id=board_id, user_id="mock-user-gamer", status="completed")
    
    mock_db = mocker.Mock()
    mocker.patch("src.api.routes.play.get_board_by_id", return_value=board)
    app.dependency_overrides[get_db] = lambda: mock_db
    
    headers = get_auth_headers(user_id="gamer")
    
    payload = {
        "sets": [],
        "unassigned": [
            {"color": "blue", "number": "5"}
        ],
        "hand": []
    }
    
    response = client.post(f"/correct/{board_id}", json=payload, headers=headers)
    assert response.status_code == 400
    assert "cannot contain unassigned tiles" in response.json()["detail"]


def test_correct_invalid_tile(mocker):
    board_id = "49701ce8-c174-4b53-855f-ef717f001ccd"
    board = MockBoard(id=board_id, user_id="mock-user-gamer", status="completed")
    
    mock_db = mocker.Mock()
    mocker.patch("src.api.routes.play.get_board_by_id", return_value=board)
    app.dependency_overrides[get_db] = lambda: mock_db
    
    headers = get_auth_headers(user_id="gamer")
    
    # number 15 is invalid
    payload = {
        "sets": [],
        "unassigned": [],
        "hand": [
            {"color": "blue", "number": "15"}
        ]
    }
    
    response = client.post(f"/correct/{board_id}", json=payload, headers=headers)
    # Pydantic or our validation will catch it
    assert response.status_code in [400, 422]
