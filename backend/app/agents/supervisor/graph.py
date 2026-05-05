from langgraph.graph import StateGraph, END, START
from langgraph.checkpoint.memory import MemorySaver
from app.agents.supervisor.state import SupervisorState
from app.agents.supervisor.planner import planner_node
from app.agents.supervisor.executor import executor_node
from app.agents.supervisor.replanner import replanner_node
from app.agents.supervisor.synthesizer import synthesizer_node

builder = StateGraph(SupervisorState)

builder.add_node("planner", planner_node)
builder.add_node("executor", executor_node)
builder.add_node("replanner", replanner_node)
builder.add_node("synthesizer", synthesizer_node)

builder.add_edge(START, "planner")
builder.add_edge("planner", "executor")
builder.add_edge("executor", "replanner")


def should_continue(state: SupervisorState) -> str:
    if state["loop_count"] >= state["max_loops"]:
        return "synthesizer"
    if state.get("should_continue"):
        return "executor"
    return "synthesizer"


builder.add_conditional_edges("replanner", should_continue, {
    "executor": "executor",
    "synthesizer": "synthesizer",
})
builder.add_edge("synthesizer", END)

graph = builder.compile(checkpointer=MemorySaver())
