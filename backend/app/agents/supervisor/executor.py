import asyncio
from langgraph.types import interrupt
from app.agents.supervisor.state import SupervisorState
from app.a2a.client import A2AClient
from app.a2a.types import JsonRpcResponse, TaskResult, TaskStatus

a2a_client = A2AClient()

# 模块级 stash：LangGraph 重放时不保证 state 直接赋值被 checkpoint 保存，
# 用模块级 dict 避开此问题。key=tid, value={task_id_on_agent, msg, agent}
_stash: dict[str, dict] = {}

_AGENT_MAP = {
    "Profile Agent":   ("profile-agent", 8001),
    "Matching Agent":  ("matching-agent", 8002),
    "Interview Agent": ("interview-agent", 8003),
    "Support Agent":   ("support-agent", 8004),
    "profile-agent":   ("profile-agent", 8001),
    "matching-agent":  ("matching-agent", 8002),
    "interview-agent": ("interview-agent", 8003),
    "support-agent":   ("support-agent", 8004),
}


def _agent_url(agent_name: str) -> str:
    svc, port = _AGENT_MAP.get(agent_name, (agent_name, 8001))
    return f"http://{svc}:{port}"


async def _execute_task(task: dict, session_id: str, client: A2AClient
                        ) -> tuple[dict, JsonRpcResponse | None]:
    """执行 A2A 任务。重放时 _stash 命中 → 合成结果避免重复 HTTP；否则正常调用。"""
    tid = task.get("task_id", task["agent"])

    if tid in _stash:
        pt = _stash[tid]
        return task, JsonRpcResponse(
            id=1,
            result=TaskResult(
                id=pt["task_id_on_agent"],
                status=TaskStatus(state="input-required", message=pt["msg"]),
            ),
        )

    url = _agent_url(task["agent"])
    data = dict(task.get("data", {}))
    # 仅 Profile Agent 注入 session_id 用于关联已上传文件；其他 Agent 不注入系统字段
    agent_name = task.get("agent", "")
    if "profile" in agent_name.lower() and session_id:
        data["session_id"] = session_id
        from app.api.agent import _parsed_files as supervisor_files
        if session_id in supervisor_files:
            data["_parsed_files"] = supervisor_files[session_id]
    try:
        result = await client.send_message(url, message={
            "role": "user",
            "parts": [
                {"type": "text", "text": f"执行任务: {task['action']}"},
                {"type": "application/json", "content": data},
            ]
        })
        return task, result
    except Exception:
        return task, None


async def executor_node(state: SupervisorState) -> dict:
    """并行 A2A + 串行中断。模块级 _stash 确保 LangGraph 重放时不重复 HTTP 调用。"""
    pending = [t for t in state["plan"]
               if t.get("task_id", t["agent"]) not in state["all_results"]]

    if not pending:
        return {"all_results": state["all_results"]}

    session_id = state.get("session_id", "")
    running = [asyncio.create_task(_execute_task(t, session_id, a2a_client))
               for t in pending]

    for coro in asyncio.as_completed(running):
        task, result = await coro
        tid = task.get("task_id", task["agent"])

        if result is None:
            state["all_results"][tid] = [{"error": "agent_unavailable"}]
            _stash.pop(tid, None)
            continue

        if result.result and result.result.status.state == "input-required":
            if tid not in _stash:
                _stash[tid] = {
                    "task_id_on_agent": result.result.id,
                    "msg": result.result.status.message or "请提供更多信息",
                    "agent": task["agent"],
                }

            task_on_agent_id = result.result.id
            msg = result.result.status.message or "请提供更多信息"

            while True:
                interrupt_payload = {
                    "type": "user_question",
                    "question": msg,
                    "task_id": task_on_agent_id,
                }
                user_answer = interrupt(interrupt_payload)
                text_to_agent = (user_answer.get("answer", "")
                                 if isinstance(user_answer, dict) else str(user_answer))
                try:
                    continued = await a2a_client.send_message(
                        agent_url=_agent_url(task["agent"]),
                        message={
                            "role": "user",
                            "parts": [{"type": "text", "text": text_to_agent}],
                        },
                        task_id=task_on_agent_id,
                    )
                except Exception:
                    state["all_results"][tid] = [{"error": "agent_resume_failed"}]
                    _stash.pop(tid, None)
                    break
                if not continued.result or continued.error:
                    state["all_results"][tid] = [{"error": "agent_resume_failed"}]
                    _stash.pop(tid, None)
                    break
                if continued.result.status.state == "input-required":
                    task_on_agent_id = continued.result.id
                    msg = continued.result.status.message or "请提供更多信息"
                    if tid in _stash:
                        _stash[tid]["task_id_on_agent"] = task_on_agent_id
                        _stash[tid]["msg"] = msg
                    continue
                if continued.result.artifacts:
                    state["all_results"][tid] = [a.content for a in continued.result.artifacts]
                else:
                    state["all_results"][tid] = []
                break

            _stash.pop(tid, None)
            task["data"] = {}

        elif result.result and result.result.status.state == "completed":
            if result.result.artifacts:
                state["all_results"][tid] = [a.content for a in result.result.artifacts]
            else:
                state["all_results"][tid] = []
            task["data"] = {}

    all_failed = all(
        isinstance(v, list) and len(v) > 0 and isinstance(v[0], dict) and "error" in v[0]
        for v in state["all_results"].values()
    ) if state["all_results"] else False
    result = {"all_results": state["all_results"]}
    if all_failed:
        result["should_continue"] = False
    return result
