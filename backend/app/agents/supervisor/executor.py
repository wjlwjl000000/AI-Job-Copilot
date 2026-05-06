import asyncio
from langgraph.types import interrupt
from app.agents.supervisor.state import SupervisorState
from app.a2a.client import A2AClient

a2a_client = A2AClient()

# Agent Card name → (Docker service name, port)
_AGENT_MAP = {
    "Profile Agent":   ("profile-agent", 8001),
    "Matching Agent":  ("matching-agent", 8002),
    "Interview Agent": ("interview-agent", 8003),
    "Support Agent":   ("support-agent", 8004),
    # Also accept service names directly
    "profile-agent":   ("profile-agent", 8001),
    "matching-agent":  ("matching-agent", 8002),
    "interview-agent": ("interview-agent", 8003),
    "support-agent":   ("support-agent", 8004),
}


def _agent_url(agent_name: str) -> str:
    svc, port = _AGENT_MAP.get(agent_name, (agent_name, 8001))
    return f"http://{svc}:{port}"


async def _execute_task(task: dict, client: A2AClient) -> tuple[dict, dict | None]:
    """执行单个 A2A 任务，返回 (task_info, result_or_none)。连接失败返回 None。"""
    url = _agent_url(task["agent"])
    try:
        result = await client.send_message(url, message={
            "role": "user",
            "parts": [
                {"type": "text", "text": f"执行任务: {task['action']}"},
                {"type": "application/json", "content": task["data"]},
            ]
        })
        return task, result
    except Exception:
        return task, None


async def executor_node(state: SupervisorState) -> dict:
    """并行 A2A 执行 Plan。input-required → interrupt() 挂起，completed → 收集 result。"""
    pending = [t for t in state["plan"] if t.get("task_id", t["agent"]) not in state["all_results"]]

    if not pending:
        return {"all_results": state["all_results"]}

    running = [asyncio.create_task(_execute_task(t, a2a_client)) for t in pending]

    for coro in asyncio.as_completed(running):
        task, result = await coro

        tid = task.get("task_id", task["agent"])
        if result is None:
            state["all_results"][tid] = [{"error": "agent_unavailable"}]
            continue

        if result.result and result.result.status.state == "input-required":
            user_answer = interrupt({
                "type": "user_question",
                "question": result.result.status.message or "请提供更多信息",
                "task_id": result.result.id,
            })
            continued = await a2a_client.send_message(
                agent_url=_agent_url(task["agent"]),
                message={
                    "role": "user",
                    "parts": [{"type": "text", "text": user_answer.get("answer", "")}],
                },
                task_id=result.result.id,
            )
            if continued.result and continued.result.artifacts:
                state["all_results"][tid] = [a.content for a in continued.result.artifacts]
            task["data"] = {}
        elif result.result and result.result.status.state == "completed":
            if result.result.artifacts:
                state["all_results"][tid] = [a.content for a in result.result.artifacts]
            else:
                state["all_results"][tid] = []
            task["data"] = {}

    # 全部 Agent 不可用时跳过 Replanner，直接让 Synthesizer 回复
    all_failed = all(
        isinstance(v, list) and len(v) > 0 and isinstance(v[0], dict) and "error" in v[0]
        for v in state["all_results"].values()
    )
    result = {"all_results": state["all_results"]}
    if all_failed:
        result["should_continue"] = False
    return result
