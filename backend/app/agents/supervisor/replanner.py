import json
from pydantic import BaseModel
from langchain_core.messages import SystemMessage, HumanMessage
from app.agents.supervisor.state import SupervisorState
from app.tools.llm import llm


class ReplanOutput(BaseModel):
    action: str  # "done" | "rewrite"
    reason: str
    revised_plan: list[dict] = []


def replanner_node(state: SupervisorState) -> dict:
    response = llm.with_structured_output(ReplanOutput).invoke([
        SystemMessage(
            "你是 Replanner。基于目标和已执行结果，决定是否继续。"
            "1. 所有步骤完成 → done"
            "2. 还有未执行步骤 → rewrite"
            "3. 不要自动追加用户未请求的任务（软连接原则）"
            f"当前第{state['loop_count']}轮，最多{state['max_loops']}轮。"
        ),
        HumanMessage(f"目标: {state['goal']}"),
        HumanMessage(f"Plan: {json.dumps(state['plan'], ensure_ascii=False)}"),
        HumanMessage(f"结果: {json.dumps(state['all_results'], ensure_ascii=False)}"),
    ])

    if response.action == "done":
        return {"should_continue": False}
    return {
        "should_continue": True,
        "plan": response.revised_plan,
        "loop_count": state["loop_count"] + 1,
    }
