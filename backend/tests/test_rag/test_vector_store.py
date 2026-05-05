import pytest
import httpx
from app.rag.vector_store import get_chroma_client, init_collections


async def _is_chroma_available() -> bool:
    from app.config import settings
    try:
        client = await get_chroma_client()
        return True
    except (ValueError, httpx.ConnectError):
        return False


@pytest.mark.asyncio
async def test_get_chroma_client_returns_client():
    await _check_chroma()
    client = await get_chroma_client()
    assert client is not None


@pytest.mark.asyncio
async def test_init_collections_creates_three():
    await _check_chroma()
    await init_collections()
    client = await get_chroma_client()
    collections = client.list_collections()
    names = [c.name for c in collections]
    assert "jobs" in names
    assert "stories" in names
    assert "profiles" in names


async def _check_chroma():
    """Helper to skip tests if Chroma server is not available."""
    try:
        client = await get_chroma_client()
    except (ValueError, httpx.ConnectError):
        pytest.skip("Chroma server is not running")
