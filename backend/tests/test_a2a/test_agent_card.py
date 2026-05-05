from app.a2a.agent_card import create_agent_card, AgentCard


def test_agent_card_has_required_fields():
    card = create_agent_card(
        agent_id="urn:agent:copilot:profile",
        name="Profile Agent",
        description="解析简历、构建画像",
        url="http://localhost:8001",
        skills=[{"id": "parse-resume", "name": "解析简历", "description": "解析文档"}],
    )
    d = card.model_dump()
    assert d["a2a_version"] == "1.0"
    assert d["id"] == "urn:agent:copilot:profile"
    assert d["name"] == "Profile Agent"
    assert len(d["skills"]) == 1
    assert d["capabilities"]["streaming"] is True


def test_agent_card_default_input_modes():
    card = create_agent_card("urn:agent:copilot:test", "Test", "Test", "http://localhost", [])
    d = card.model_dump()
    assert "text" in d["defaultInputModes"]
    assert "application/json" in d["defaultInputModes"]
