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

    # ── 重放路径：模块级 _stash 命中 → 合成结果 ──
    if tid in _stash:
        pt = _stash[tid]
        print(f"[executor] _execute_task STASH tid={tid} task_id_on_agent={pt['task_id_on_agent']} msg={pt['msg'][:50]!r}")
        return task, JsonRpcResponse(
            id=1,
            result=TaskResult(
                id=pt["task_id_on_agent"],
                status=TaskStatus(state="input-required", message=pt["msg"]),
            ),
        )

    # ── 正常路径：HTTP 调用 ──
    url = _agent_url(task["agent"])
    print(f"[executor] _execute_task HTTP tid={tid} url={url} action={task.get('action','')}")
    data = dict(task.get("data", {}))
    if session_id:
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
        print(f"[executor] _execute_task DONE tid={tid} state={(result.result and result.result.status.state) if result else 'NO_RESULT'}")
        return task, result
    except Exception as e:
        print(f"[executor] _execute_task FAIL tid={tid} {type(e).__name__}: {e}")
        return task, None


async def executor_node(state: SupervisorState) -> dict:
    """并行 A2A + 串行中断。模块级 _stash 确保 LangGraph 重放时不重复 HTTP 调用。"""
    pending = [t for t in state["plan"]
               if t.get("task_id", t["agent"]) not in state["all_results"]]

    stash_summary = [(k, v["msg"][:30]) for k, v in _stash.items()]
    print(f"[executor] NODE_ENTER _stash={stash_summary} "
          f"pending={[t.get('task_id','?') for t in pending]} all_results_keys={list(state['all_results'].keys())}")

    if not pending:
        return {"all_results": state["all_results"]}

    session_id = state.get("session_id", "")
    running = [asyncio.create_task(_execute_task(t, session_id, a2a_client))
               for t in pending]

    for coro in asyncio.as_completed(running):
        task, result = await coro
        tid = task.get("task_id", task["agent"])
        print(f"[executor] TASK_DONE tid={tid} result_is_none={result is None} "
              f"state={(result.result and result.result.status.state) if (result and result.result) else 'N/A'}")

        if result is None:
            state["all_results"][tid] = [{"error": "agent_unavailable"}]
            continue

        if result.result and result.result.status.state == "input-required":
            # 首次中断 → 写入模块级 _stash（重放时 _execute_task 用它生成合成结果）
            if tid not in _stash:
                _stash[tid] = {
                    "task_id_on_agent": result.result.id,
                    "msg": result.result.status.message or "请提供更多信息",
                    "agent": task["agent"],
                }
                print(f"[executor] STASH_SAVE tid={tid}")

            task_on_agent_id = result.result.id
            msg = result.result.status.message or "请提供更多信息"

            # ── 中断循环（首次 + 重放走完全相同的代码路径）──
            loop_count = 0
            while True:
                loop_count += 1
                print(f"[executor] INT_LOOP tid={tid} iter={loop_count} task_on_agent_id={task_on_agent_id} msg={msg[:50]!r}")
                interrupt_payload = {
                    "type": "user_question",
                    "question": msg,
                    "task_id": task_on_agent_id,
                }
                user_answer = interrupt(interrupt_payload)
                print(f"[executor] INT_RESUMED tid={tid} user_answer={user_answer!r}")
                text_to_agent = (user_answer.get("answer", "")
                                 if isinstance(user_answer, dict) else str(user_answer))
                print(f"[executor] SEND_TO_AGENT tid={tid} text={text_to_agent!r} task_id={task_on_agent_id}")
                try:
                    continued = await a2a_client.send_message(
                        agent_url=_agent_url(task["agent"]),
                        message={
                            "role": "user",
                            "parts": [{"type": "text", "text": text_to_agent}],
                        },
                        task_id=task_on_agent_id,
                    )
                except Exception as e:
                    print(f"[executor] SEND_FAIL tid={tid} {type(e).__name__}: {e}")
                    state["all_results"][tid] = [{"error": "agent_resume_failed"}]
                    break
                cont_state = continued.result.status.state if continued.result else 'NO_RESULT'
                print(f"[executor] AGENT_RESP tid={tid} state={cont_state}")
                if not continued.result or continued.error:
                    state["all_results"][tid] = [{"error": "agent_resume_failed"}]
                    break
                if continued.result.status.state == "input-required":
                    task_on_agent_id = continued.result.id
                    msg = continued.result.status.message or "请提供更多信息"
                    print(f"[executor] INT_LOOP_CONTINUE tid={tid} next_msg={msg[:50]!r}")
                    # 更新 _stash → 下次重放时返回最新上下文
                    if tid in _stash:
                        _stash[tid]["task_id_on_agent"] = task_on_agent_id
                        _stash[tid]["msg"] = msg
                    continue
                if continued.result.artifacts:
                    state["all_results"][tid] = [a.content for a in continued.result.artifacts]
                else:
                    state["all_results"][tid] = []
                break
            print(f"[executor] INT_LOOP_DONE tid={tid} all_results_ok={bool(state['all_results'].get(tid))}")

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
