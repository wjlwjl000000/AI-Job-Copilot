import json
from app.agents.supervisor.state import SupervisorState
from app.tools.llm import llm

REPLANNER_PROMPT = """你是计划评估与调整专家（Replanner）。你的职责是：检查每个子任务的执行结果，判断当前计划是否需要调整。

## 规则描述
- 逐项检查plan中每个task的执行结果（results）
- 如果所有任务都已完成且结果有效 → action: "done"
- 如果部分任务失败或结果不满足要求，且还有剩余循环次数 → action: "rewrite"，生成revised_plan
- 如果已达到最大循环次数({max_loops}) → action: "done"（即使有任务未完美完成）
- 当前循环：{loop}/{max_loops}

## 规则约束
- 不要因为结果"不够完美"而无限制重试，关键信息已获取即可完成
- 如果所有结果都是error，直接done，不要rewrite
- 不要在revised_plan中追加用户未请求的新任务
- 不要修改原始任务的核心意图

## 输出约束
- 必须输出纯JSON（不含markdown代码块标记）
- done时：{{"action": "done", "reason": "简述完成原因"}}
- rewrite时：{{"action": "rewrite", "reason": "简述需要调整的原因", "revised_plan": [...]}}
- revised_plan格式与原始plan一致
- reason用中文

当前计划: {plan}
执行结果: {results}
循环: {loop}/{max_loops}"""


def replanner_node(state: SupervisorState) -> dict:
    results = state.get("all_results", {})
    if results and all(
        isinstance(v, list) and len(v) > 0 and isinstance(v[0], dict) and "error" in v[0]
        for v in results.values()
    ):
        return {"should_continue": False}

    # Compact prompt to stay under 4096 token limit
    prompt = REPLANNER_PROMPT.format(
        plan=json.dumps(state["plan"], ensure_ascii=False),
        results=json.dumps(state["all_results"], ensure_ascii=False),
        loop=state["loop_count"],
        max_loops=state["max_loops"],
    )
    raw = llm.invoke(prompt).content
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
