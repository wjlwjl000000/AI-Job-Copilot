import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.agents.supervisor.state import SupervisorState
from app.agents.supervisor.executor import executor_node


@pytest.mark.asyncio
async def test_executor_handles_completed():
    state: SupervisorState = {
        "user_id": "u1", "messages": [], "goal": "test",
        "plan": [{"agent": "profile-agent", "action": "parse", "data": {}, "depends_on": []}],
        "all_results": {}, "loop_count": 0, "max_loops": 3,
        "should_continue": False, "synthesized_response": "",
    }
    mock_result = MagicMock()
    mock_result.result.id = "task-abc"
    mock_result.result.status.state = "completed"
    mock_result.result.artifacts = [MagicMock(content={"result": "ok"})]

    with patch("app.agents.supervisor.executor.a2a_client.send_message", new_callable=AsyncMock) as mock_send:
        mock_send.return_value = mock_result
        result = await executor_node(state)
        assert "profile-agent" in result["all_results"]


@pytest.mark.asyncio
async def test_executor_handles_input_required():
    state: SupervisorState = {
        "user_id": "u1", "messages": [], "goal": "test",
        "plan": [{"agent": "profile-agent", "action": "parse", "data": {}, "depends_on": []}],
        "all_results": {}, "loop_count": 0, "max_loops": 3,
        "should_continue": False, "synthesized_response": "",
    }
    mock_result = MagicMock()
    mock_result.result.id = "task-abc"
    mock_result.result.status.state = "input-required"
    mock_result.result.status.message = "请补充学历信息"

    mock_continued = MagicMock()
    mock_continued.result.artifacts = [MagicMock(content={"result": "continued ok"})]

    with patch("app.agents.supervisor.executor.a2a_client.send_message", new_callable=AsyncMock) as mock_send:
        mock_send.side_effect = [mock_result, mock_continued]
        with patch("app.agents.supervisor.executor.interrupt") as mock_interrupt:
            mock_interrupt.return_value = {"answer": "北京大学"}
            await executor_node(state)
            mock_interrupt.assert_called_once()
