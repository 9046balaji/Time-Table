import pytest
from httpx import AsyncClient, ASGITransport
from main import app


@pytest.mark.asyncio
async def test_auth_login_and_profile_flow():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Login with valid credentials
        login_res = await client.post(
            "/api/v1/auth/login",
            json={"username": "coordinator@vfstr.ac.in", "password": "SecretPassword123"}
        )
        assert login_res.status_code == 200
        data = login_res.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["role"] == "DEPT_COORDINATOR"
        token = data["access_token"]

        # 2. Get profile with Bearer token
        profile_res = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert profile_res.status_code == 200
        pdata = profile_res.json()
        assert pdata["username"] == "coordinator@vfstr.ac.in"
        assert pdata["role"] == "DEPT_COORDINATOR"
        assert pdata["authenticated"] is True

        # 3. Test OAuth2 password form login endpoint
        form_res = await client.post(
            "/api/v1/auth/token",
            data={"username": "hod@vfstr.ac.in", "password": "HodPassword123"}
        )
        assert form_res.status_code == 200
        fdata = form_res.json()
        assert fdata["role"] == "HOD"

        # 4. Invalid credentials check
        bad_res = await client.post(
            "/api/v1/auth/login",
            json={"username": "", "password": ""}
        )
        assert bad_res.status_code == 400
