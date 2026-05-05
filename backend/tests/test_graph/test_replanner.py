from app.agents.supervisor.replanner import replanner_node


def test_replanner_node_callable():
    assert callable(replanner_node)
