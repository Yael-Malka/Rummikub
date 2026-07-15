"""Auth route integration tests."""

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio

async def test_register_user(client: AsyncClient):
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "test@example.com",
            "password": "strongpassword123",
            "full_name": "Test User"
        }
    )
    assert response.status_code == 201
    assert response.json()["message"] == "Verification email sent"

async def test_login_user(client: AsyncClient):
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "test@example.com",
            "password": "strongpassword123"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
