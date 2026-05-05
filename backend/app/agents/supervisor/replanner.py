import json
from langchain_core.messages import SystemMessage, HumanMessage
from app.agents.supervisor.state import SupervisorState
from app.tools.llm import llm

REPLANNER_PROMPT = """你是 Replanner。基于目标和已执行结果，决定是否继续。输出纯 JSON（不要markdown代码块）。

规则:
1. 所有步骤完成 → action: "done"
2. 还有未执行步骤 → action: "rewrite"，并提供 revised_plan
3. 不要自动追加用户未请求的任务（软连接原则）

当前第{loop_count}轮，最多{max_loops}轮。

输出格式:
{{"action": "done|rewrite", "reason": "...", "revised_plan": [...]}}"""


def replanner_node(state: SupervisorState) -> dict:
    # 所有结果都是 error → 直接结束，避免死循环
    results = state.get("all_results", {})
    if results and all(
        isinstance(v, list) and len(v) > 0 and isinstance(v[0], dict) and "error" in v[0]
        for v in results.values()
    ):
        return {"should_continue": False}

    prompt = REPLANNER_PROMPT.format(
        loop_count=state["loop_count"],
        max_loops=state["max_loops"],
    )

    context = (
        f"目标: {state['goal']}\n"
        f"Plan: {json.dumps(state['plan'], ensure_ascii=False)}\n"
        f"结果: {json.dumps(state['all_results'], ensure_ascii=False)}"
    )

    raw = llm.invoke([SystemMessage(content=prompt), HumanMessage(content=context)]).content
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[-1].rsplit("\n```", 1)[0]

    try:
        response = json.loads(raw)
    except json.JSONDecodeError:
        return {"should_continue": False}

    if response.get("action") == "done":
        return {"should_continue": False}
    return {
        "should_continue": True,
        "plan": response.get("revised_plan", []),
        "loop_count": state["loop_count"] + 1,
    }
