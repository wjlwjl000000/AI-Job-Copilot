import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_get_profile_endpoint_exists():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/profile")
    assert response.status_code != 404


@pytest.mark.asyncio
async def test_put_profile_endpoint_exists():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.put("/api/profile", json={"work_years": 3})
    assert response.status_code != 404
