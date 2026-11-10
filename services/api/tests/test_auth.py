import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_and_login_flow(async_client: AsyncClient):
    # 1. Register new user
    reg_payload = {
        "email": "newathlete@example.com",
        "password": "SecurePassword123!",
        "full_name": "New Athlete"
    }
    reg_resp = await async_client.post("/api/v1/auth/register", json=reg_payload)
    assert reg_resp.status_code == 201
    reg_data = reg_resp.json()
    assert "access_token" in reg_data
    assert reg_data["user"]["email"] == "newathlete@example.com"

    # 2. Login with registered credentials
    login_payload = {
        "email": "newathlete@example.com",
        "password": "SecurePassword123!"
    }
    login_resp = await async_client.post("/api/v1/auth/login", json=login_payload)
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]

    # 3. Access protected /auth/me route
    headers = {"Authorization": f"Bearer {token}"}
    me_resp = await async_client.get("/api/v1/auth/me", headers=headers)
    assert me_resp.status_code == 200
    assert me_resp.json()["email"] == "newathlete@example.com"


@pytest.mark.asyncio
async def test_duplicate_registration_rejected(async_client: AsyncClient):
    payload = {
        "email": "duplicate@example.com",
        "password": "Password123!",
        "full_name": "Duplicate Test"
    }
    res1 = await async_client.post("/api/v1/auth/register", json=payload)
    assert res1.status_code == 201

    res2 = await async_client.post("/api/v1/auth/register", json=payload)
    assert res2.status_code == 400
    assert "already exists" in res2.json()["detail"]


@pytest.mark.asyncio
async def test_invalid_login(async_client: AsyncClient):
    login_payload = {
        "email": "nonexistent@example.com",
        "password": "WrongPassword!"
    }
    resp = await async_client.post("/api/v1/auth/login", json=login_payload)
    assert resp.status_code == 401
