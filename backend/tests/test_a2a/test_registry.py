import pytest
from unittest.mock import AsyncMock, patch
from app.a2a.registry import AgentRegistry
from app.a2a.client import A2AClient


@pytest.mark.asyncio
async def test_registry_discover():
    client = A2AClient()
    fake_card = {"name": "profile-agent", "description": "parse resumes", "skills": [], "url": "http://localhost:8001"}
    with patch.object(client, 'fetch_agent_card', AsyncMock(return_value=fake_card)):
        registry = AgentRegistry(client=client)
        await registry.discover(["http://localhost:8001"])
        assert "profile-agent" in registry._agents


@pytest.mark.asyncio
async def test_get_all_summaries_excludes_support():
    client = A2AClient()
    registry = AgentRegistry(client=client)
    registry._agents = {
        "profile-agent": {"name": "profile-agent", "description": "...", "skills": []},
        "matching-agent": {"name": "matching-agent", "description": "...", "skills": []},
        "support-agent": {"name": "support-agent", "description": "...", "skills": []},
    }
    summaries = registry.get_all_summaries()
    names = [s["name"] for s in summaries]
    assert "profile-agent" in names
    assert "matching-agent" in names
    assert "support-agent" not in names


def test_is_system_agent():
    registry = AgentRegistry()
    assert registry.is_system_agent("profile-agent") is True
    assert registry.is_system_agent("custom-agent") is False
