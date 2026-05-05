from app.agents.supervisor.state import SupervisorState
from app.agents.supervisor.planner import planner_node, PlanTask, PlanSchema


def test_planner_node_is_callable():
    assert callable(planner_node)


def test_plan_task_model():
    task = PlanTask(agent="profile-agent", action="parse", data={"file_path": "test.pdf"}, depends_on=[])
    assert task.agent == "profile-agent"
    assert task.action == "parse"
    assert task.depends_on == []


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
