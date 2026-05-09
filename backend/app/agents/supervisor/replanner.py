import json
from app.agents.supervisor.state import SupervisorState
from app.tools.llm import llm

REPLANNER_PROMPT = """你是计划评估与调整专家（Replanner）。检查每个子任务的执行结果，判断当前计划是否需要调整。

## 规则描述
- 逐项检查plan中每个task的执行结果（results）
- 所有任务已完成且结果有效 → action: "done"
- 部分任务失败且未达最大循环 → action: "rewrite"
- 已达最大循环({max_loops}) → action: "done"

## 规则约束
- 只能使用原始plan中已有的 Agent 名称，禁止虚构新 Agent。
- 只能基于原始plan重写 task 的 action 和 data 内容，或添加新 task。
- 每个 task 的格式必须与原始plan完全一致：{{"task_id": "字符串", "agent": "已有Agent名", "action": "字符串", "data": {{...}}, "depends_on": []}}
- 不得修改 task_id 格式，不得新增字段，不得删除已有字段。
- 不要在 revised_plan 中追加用户未请求的新任务。
- 所有结果都是 error → 直接 done，不要 rewrite。

## 输出约束
- 纯JSON（无markdown代码块）
- done: {{"action": "done", "reason": "..."}}
- rewrite: {{"action": "rewrite", "reason": "...", "revised_plan": [原始格式的task数组]}}
- reason 用中文

当前计划: {plan}
执行结果: {results}
循环: {loop}/{max_loops}"""


async def replanner_node(state: SupervisorState) -> dict:
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
    raw = (await llm.ainvoke(prompt)).content
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[-1].rsplit("\n```", 1)[0]

    try:
        response = json.loads(raw)
    except json.JSONDecodeError:
        return {"should_continue": False}

    if response.get("action") == "done":
        return {"should_continue": False}

    # rewrite: 给 revised_plan 中 task_id 已存在于 all_results 的 task 分配新 ID，避免 executor 跳过
    revised = response.get("revised_plan", [])
    loop = state["loop_count"] + 1
    for i, t in enumerate(revised):
        old_id = t.get("task_id", "")
        if old_id in state.get("all_results", {}):
            t["task_id"] = f"{old_id}_r{loop}"
    return {
        "should_continue": True,
        "plan": revised,
        "loop_count": loop,
    }
