from typing import TypedDict, Annotated
from langgraph.graph.message import add_messages


class SupervisorState(TypedDict):
    user_id: str
    session_id: str
    messages: Annotated[list, add_messages]
    goal: str
    plan: list[dict]
    all_results: dict
    synthesized_response: str
    loop_count: int
    max_loops: int
    should_continue: bool
