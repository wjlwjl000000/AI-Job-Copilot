import pytest
from unittest.mock import AsyncMock, patch
from app.a2a.client import A2AClient
from app.a2a.types import JsonRpcResponse, TaskResult, TaskStatus


@pytest.mark.asyncio
async def test_send_message_returns_task_result():
    mock_response = JsonRpcResponse(
        id=1,
        result=TaskResult(id="task-abc", status=TaskStatus(state="completed"), artifacts=[]),
    )
    client = A2AClient()
    with patch.object(client, '_post', AsyncMock(return_value=mock_response)):
        result = await client.send_message(
            agent_url="http://test:8001",
            message={"role": "user", "parts": [{"type": "text", "text": "hello"}]},
        )
    assert result.result.id == "task-abc"
    assert result.result.status.state == "completed"


@pytest.mark.asyncio
async def test_fetch_agent_card():
    card_data = {"a2a_version": "1.0", "id": "urn:agent:test", "name": "Test", "url": "http://test"}
    client = A2AClient()
    with patch.object(client, '_get', AsyncMock(return_value=card_data)):
        card = await client.fetch_agent_card("http://test:8001")
    assert card["name"] == "Test"
