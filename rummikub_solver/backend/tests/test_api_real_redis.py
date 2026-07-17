"""API tests against a real Redis instance."""

import io
from httpx import ASGITransport, AsyncClient
import pytest
from src.main import app


from src.core.redis import close_redis_pool


@pytest.mark.anyio
async def test_real_redis_integration_flow(mocker):
    """Verify end-to-end flow with real Redis connection."""
    mocker.patch("src.services.play_service.celery_app.send_task")
    await close_redis_pool()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1. Log in to obtain a JWT session token
        login_payload = {"email": "real-redis-user@example.com", "password": "Passw0rd!"}
        login_response = await ac.post("/login", json=login_payload)
        assert login_response.status_code == 200
        access_token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {access_token}"}


        # 2. Upload dummy image data to /send-play
        image_bytes = b"fake-jpeg-image-bytes"
        files = {
            "board_image": (
                "test_real_redis_board.jpg",
                io.BytesIO(image_bytes),
                "image/jpeg",
            ),
            "hand_image": (
                "test_real_redis_hand.jpg",
                io.BytesIO(image_bytes),
                "image/jpeg",
            )
        }
        upload_response = await ac.post("/send-play", headers=headers, files=files)
        assert upload_response.status_code == 200
        upload_data = upload_response.json()
        assert "id" in upload_data
        assert upload_data["status"] == "processing"
        play_id = upload_data["id"]

        # Simulate Celery worker finishing by writing to real Redis
        from redis.asyncio import Redis
        from src.core.config import settings
        import json
        r = Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT)
        await r.set(
            f"boards:{play_id}",
            json.dumps({
                "status": "completed",
                "result": {
                    "sets": [],
                    "unassigned": [],
                    "hand": []
                },
                "error": None
            })
        )
        await r.aclose()

        # 3. Retrieve the play from /next-play/{id} (fetching from real Redis)
        retrieval_response = await ac.get(f"/next-play/{play_id}", headers=headers)
        assert retrieval_response.status_code == 200
        play_data = retrieval_response.json()
        assert play_data["id"] == play_id
        assert isinstance(play_data["result"], dict)


        # 4. Log out (blacklists the token in real Redis)
        logout_response = await ac.get("/logout", headers=headers)
        assert logout_response.status_code == 200

        # 5. Verify token is now blacklisted in real Redis (should return 401)
        unauth_response = await ac.get("/logout", headers=headers)
        assert unauth_response.status_code == 401
