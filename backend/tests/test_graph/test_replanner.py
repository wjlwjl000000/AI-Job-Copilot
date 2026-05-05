from app.agents.supervisor.replanner import replanner_node, ReplanOutput


def test_replanner_node_callable():
    assert callable(replanner_node)


def test_replan_output_model():
    output = ReplanOutput(action="done", reason="all tasks completed")
    assert output.action == "done"
    assert output.reason == "all tasks completed"


def test_replan_output_rewrite():
    output = ReplanOutput(action="rewrite", reason="need more tasks", revised_plan=[{"agent": "profile", "action": "build"}])
    assert len(output.revised_plan) == 1
