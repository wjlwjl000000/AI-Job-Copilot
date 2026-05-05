import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_create_application_endpoint_exists():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/applications", json={"job_id": "j-1"})
    assert response.status_code != 404


@pytest.mark.asyncio
async def test_list_applications_endpoint_exists():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/applications")
    assert response.status_code != 404


@pytest.mark.asyncio
async def test_stats_endpoint_exists():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/applications/stats")
    assert response.status_code != 404
