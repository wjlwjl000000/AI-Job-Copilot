import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_upload_resume_endpoint_exists():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/resumes/upload")
    assert response.status_code != 404


@pytest.mark.asyncio
async def test_list_resumes_endpoint_exists():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/resumes")
    assert response.status_code != 404
