from app.agents.profile.agent import profile_agent, PROFILE_SYSTEM_PROMPT


def test_profile_agent_created():
    assert profile_agent is not None


def test_system_prompt_has_placeholders():
    assert "{skills_list}" in PROFILE_SYSTEM_PROMPT
    assert "{skill_content}" in PROFILE_SYSTEM_PROMPT


def test_profile_agent_has_all_tools():
    tool_names = [t.name for t in profile_agent.tools]
    assert "parse_document" in tool_names
    assert "db_read" in tool_names
    assert "db_write" in tool_names
    assert "call_llm" in tool_names
    assert "chroma_insert" in tool_names
