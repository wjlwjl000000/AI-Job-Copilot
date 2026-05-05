import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_get_job_endpoint_exists():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/jobs/j-1")
    assert response.status_code != 404


@pytest.mark.asyncio
async def test_create_job_endpoint_exists():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/jobs", json={"title": "test"})
    assert response.status_code != 404
