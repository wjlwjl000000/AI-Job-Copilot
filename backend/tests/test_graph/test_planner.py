from app.agents.supervisor.state import SupervisorState
from app.agents.supervisor.planner import planner_node, DummyRegistry


def test_planner_node_is_callable():
    assert callable(planner_node)


def test_dummy_registry_has_three_agents():
    reg = DummyRegistry()
    cards = reg.get_all_summaries()
    assert len(cards) == 3
    names = [c["name"] for c in cards]
    assert "profile-agent" in names
    assert "matching-agent" in names
    assert "interview-agent" in names


def test_supervisor_state_fields():
    state: SupervisorState = {
        "user_id": "u1",
        "messages": [],
        "goal": "",
        "plan": [],
        "all_results": {},
        "synthesized_response": "",
        "loop_count": 0,
        "max_loops": 3,
        "should_continue": False,
    }
    assert state["max_loops"] == 3
    assert state["loop_count"] == 0
