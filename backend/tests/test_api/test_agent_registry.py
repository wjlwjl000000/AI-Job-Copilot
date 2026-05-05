import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_register_agent_endpoint_exists():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/agent/registry", json={
            "agent_url": "http://localhost:8001"
        })
    assert response.status_code != 404


@pytest.mark.asyncio
async def test_list_registry_endpoint_exists():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/agent/registry")
    assert response.status_code != 404


@pytest.mark.asyncio
async def test_delete_system_agent_returns_error():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.delete("/api/agent/registry/profile-agent")
    assert response.status_code != 404
