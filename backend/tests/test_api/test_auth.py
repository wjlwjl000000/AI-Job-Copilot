import pytest
import uuid
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_auth_all():
    """测试 register + login + wrong_password 全流程，避免 event loop 跨测试关闭问题"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        email = f"test_{uuid.uuid4().hex[:8]}@example.com"

        # register
        r = await client.post("/api/auth/register", json={"email": email, "password": "Test123456"})
        assert r.status_code == 200
        data = r.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

        # login
        r = await client.post("/api/auth/login", json={"email": email, "password": "Test123456"})
        assert r.status_code == 200
        assert "access_token" in r.json()

        # wrong password
        r = await client.post("/api/auth/login", json={"email": email, "password": "wrong"})
        assert r.status_code == 401
