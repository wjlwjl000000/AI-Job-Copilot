import asyncio
from langgraph.types import interrupt
from app.agents.supervisor.state import SupervisorState
from app.a2a.client import A2AClient

a2a_client = A2AClient()


async def _execute_task(task: dict, client: A2AClient) -> tuple[dict, object]:
    """执行单个 A2A 任务，返回 (task_info, result)。"""
    agent_url = f"http://{task['agent']}:8001"
    result = await client.send_message(agent_url, message={
        "role": "user",
        "parts": [
            {"type": "text", "text": f"执行任务: {task['action']}"},
            {"type": "application/json", "content": task["data"]},
        ]
    })
    return task, result


async def executor_node(state: SupervisorState) -> dict:
    """并行 A2A 执行 Plan。input-required → interrupt() 挂起，completed → 收集 result。"""
    pending = [t for t in state["plan"] if t["agent"] not in state["all_results"]]

    if not pending:
        return {"all_results": state["all_results"]}

    running = [asyncio.create_task(_execute_task(t, a2a_client)) for t in pending]

    for coro in asyncio.as_completed(running):
        task, result = await coro

        if result.result and result.result.status.state == "input-required":
            user_answer = interrupt({
                "type": "user_question",
                "question": result.result.status.message or "请提供更多信息",
                "task_id": result.result.id,
            })
            continued = await a2a_client.send_message(
                agent_url=f"http://{task['agent']}:8001",
                message={
                    "role": "user",
                    "parts": [{"type": "text", "text": user_answer.get("answer", "")}],
                },
                task_id=result.result.id,
            )
            if continued.result and continued.result.artifacts:
                state["all_results"][task["agent"]] = [a.content for a in continued.result.artifacts]
        elif result.result and result.result.status.state == "completed":
            if result.result.artifacts:
                state["all_results"][task["agent"]] = [a.content for a in result.result.artifacts]
            else:
                state["all_results"][task["agent"]] = []

    return {"all_results": state["all_results"]}
