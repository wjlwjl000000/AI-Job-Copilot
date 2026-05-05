from app.agents.support.agent import support_agent, SUPPORT_SYSTEM_PROMPT


def test_support_agent_never_input_required():
    """Support Agent 永远不返回 input-required"""
    assert "input-required" not in SUPPORT_SYSTEM_PROMPT.lower() or "永远不返回" in SUPPORT_SYSTEM_PROMPT


def test_support_agent_has_required_tools():
    tool_names = [t.name for t in support_agent.tools]
    assert "chroma_query" in tool_names
    assert "db_read" in tool_names
    assert "call_llm" in tool_names
    # Support 不应有 call_support_agent（不能自己调自己）
    assert "call_support_agent" not in tool_names


def test_support_agent_prompt_has_placeholders():
    assert "{skills_list}" in SUPPORT_SYSTEM_PROMPT
    assert "{skill_content}" in SUPPORT_SYSTEM_PROMPT
