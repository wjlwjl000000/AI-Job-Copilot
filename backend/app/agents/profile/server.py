from fastapi import FastAPI
from app.a2a.server import create_a2a_router, mount_agent_card
from app.a2a.agent_card import create_agent_card
from app.a2a.types import JsonRpcResponse, TaskResult, TaskStatus, TaskArtifact

app = FastAPI(title="Profile Agent")

agent_card = create_agent_card(
    agent_id="urn:agent:copilot:profile",
    name="Profile Agent",
    description="当用户提供了简历文本、个人技能描述、目标岗位方向、或要求构建/更新求职画像时调用。接收简历内容和目标岗位偏好，构建技能图谱、经验向量和竞争力评分存入知识库。不要用于职位搜索、JD匹配、简历优化或面试准备场景。需要：简历文本或文件路径、目标岗位方向（可选）。",
    url="http://localhost:8001",
    skills=[
        # {"id": "parse-resume", "name": "简历解析", "description": "解析PDF/Word/文本简历为结构化信息", "examples": ["帮我看看我的简历"]},
        {"id": "build-profile", "name": "构建画像", "description": "基于简历内容构建求职者技能画像和评分", "examples": ["帮我生成求职画像"]},
    ],
)

mount_agent_card(app, agent_card.model_dump())

# task_id → {config, sid}
_task_sessions: dict[str, dict] = {}


async def handle_task(request):
    from app.agents.profile.agent import profile_agent
    from langchain_core.messages import HumanMessage
    from langgraph.types import Command
    from app.tools.parser import set_session_id
    from app.api.agent import _parsed_files

    task_id = request.params.get("taskId") or "task-profile"

    msg_parts = request.params["message"]["parts"]
    text = " ".join([p.get("text", "") for p in msg_parts if p["type"] == "text"])
    data = {}
    for p in msg_parts:
        if p["type"] == "application/json":
            data.update(p.get("content", {}))

    if task_id in _task_sessions:
        # 恢复模式
        session = _task_sessions.pop(task_id)
        sid = session["sid"]
        config = session["config"]
        user_text = text.strip().lower()
        decision = "approve" if user_text in ("是", "确认", "yes", "ok", "覆盖", "同意") else "reject"
        result = await profile_agent.ainvoke(
            Command(resume={"decisions": [{"type": decision}]}), config
        )
        ai_msgs = [m for m in result.get("messages", []) if getattr(m, "type", "") == "ai"]
        answer = ai_msgs[-1].content if ai_msgs else str(result)
        if sid and "Final Answer" in answer:
            _parsed_files.pop(sid, None)
        return JsonRpcResponse(
            id=request.id,
            result=TaskResult(
                id=task_id,
                status=TaskStatus(state="completed"),
                artifacts=[TaskArtifact(content={"result": answer})],
            ),
        )

    # 首次执行
    sid = data.pop("session_id", None)
    parsed = data.pop("_parsed_files", None)
    if sid:
        set_session_id(sid)
    if parsed:
        _parsed_files[sid] = parsed

    prompt = f"{text}\n任务数据: {data}" if data else text
    config = {"configurable": {"thread_id": task_id}}
    result = await profile_agent.ainvoke({"messages": [HumanMessage(content=prompt)]}, config)
    # 检查是否触发中断
    interrupts = result.get("__interrupt__")
    print(f"[profile agent]:" + interrupts)
    if interrupts:
        _task_sessions[task_id] = {"config": config, "sid": sid}
        action_requests = interrupts[0].value.get("action_requests", []) if hasattr(interrupts[0], "value") else []
        message = action_requests[0].get("args", {}).get("messages", "是否确认？") if action_requests else "是否确认？"
        return JsonRpcResponse(
            id=request.id,
            result=TaskResult(
                id=task_id,
                status=TaskStatus(state="input-required", message=message),
            ),
        )

    ai_msgs = [m for m in result.get("messages", []) if getattr(m, "type", "") == "ai"]
    answer = ai_msgs[-1].content if ai_msgs else str(result)
    if sid and "Final Answer" in answer:
        _parsed_files.pop(sid, None)
    return JsonRpcResponse(
        id=request.id,
        result=TaskResult(
            id=task_id,
            status=TaskStatus(state="completed"),
            artifacts=[TaskArtifact(content={"result": answer})],
        ),
    )


app.include_router(create_a2a_router(handler=handle_task))
