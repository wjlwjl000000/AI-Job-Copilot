import pytest
from unittest.mock import AsyncMock, patch
from langchain_openai import ChatOpenAI
from app.tools.llm import call_llm


def test_call_llm_is_langchain_tool():
    assert hasattr(call_llm, 'name')
    assert call_llm.name == "call_llm"


@pytest.mark.asyncio
@patch.object(ChatOpenAI, "ainvoke", new_callable=AsyncMock)
async def test_call_llm_returns_response(mock_ainvoke):
    mock_ainvoke.return_value.content = "test response"
    result = await call_llm.ainvoke({"prompt": "hello"})
    assert result == "test response"
