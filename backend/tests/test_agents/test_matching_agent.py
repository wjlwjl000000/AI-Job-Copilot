from app.agents.matching.agent import matching_agent, MATCHING_SYSTEM_PROMPT


def test_matching_agent_has_call_support_tool():
    tool_names = [t.name for t in matching_agent.tools]
    assert "chroma_query" in tool_names
    assert "call_support_agent" in tool_names
    assert "call_llm" in tool_names
    assert "db_read" in tool_names
    assert "db_write" in tool_names


def test_matching_prompt_includes_low_match_rule():
    assert "0.6" in MATCHING_SYSTEM_PROMPT
    assert "call_support_agent" in MATCHING_SYSTEM_PROMPT


def test_prompt_has_placeholders():
    assert "{skills_list}" in MATCHING_SYSTEM_PROMPT
    assert "{skill_content}" in MATCHING_SYSTEM_PROMPT
