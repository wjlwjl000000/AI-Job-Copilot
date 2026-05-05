import pytest
from app.agents.supervisor.synthesizer import synthesizer_node


@pytest.mark.asyncio
async def test_synthesizer_node_callable():
    assert callable(synthesizer_node)
