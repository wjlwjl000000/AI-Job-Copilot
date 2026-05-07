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


async def handle_task(request):
    from app.agents.profile.agent import profile_agent
    from langchain_core.messages import HumanMessage
    msg_parts = request.params["message"]["parts"]
    text = " ".join([p.get("text", "") for p in msg_parts if p["type"] == "text"])
    data = {}
    for p in msg_parts:
        if p["type"] == "application/json":
            data.update(p.get("content", {}))
    prompt = f"{text}\n任务数据: {data}" if data else text
    result = await profile_agent.ainvoke({"messages": [HumanMessage(content=prompt)]})
    ai_msgs = [m for m in result.get("messages", []) if getattr(m, "type", "") == "ai"]
    answer = ai_msgs[-1].content if ai_msgs else str(result)
    return JsonRpcResponse(
        id=request.id,
        result=TaskResult(
            id="task-profile",
            status=TaskStatus(state="completed"),
            artifacts=[TaskArtifact(content={"result": answer})],
        ),
    )


app.include_router(create_a2a_router(handler=handle_task))
