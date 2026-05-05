from fastapi import FastAPI
from app.a2a.server import create_a2a_router, mount_agent_card
from app.a2a.agent_card import create_agent_card
from app.a2a.types import JsonRpcResponse, TaskResult, TaskStatus, TaskArtifact

app = FastAPI(title="Profile Agent")

agent_card = create_agent_card(
    agent_id="urn:agent:copilot:profile",
    name="Profile Agent",
    description="负责解析简历文件和构建用户求职画像。当用户上传简历、需要更新个人资料时调用。",
    url="http://localhost:8001",
    skills=[
        {"id": "parse-resume", "name": "简历解析", "description": "解析PDF/Word/文本简历为结构化信息", "examples": ["帮我看看我的简历"]},
        {"id": "build-profile", "name": "构建画像", "description": "基于简历内容构建求职者技能画像和评分", "examples": ["帮我生成求职画像"]},
    ],
)

mount_agent_card(app, agent_card.model_dump())


async def handle_task(request):
    from app.agents.profile.agent import profile_agent
    from langchain_core.messages import HumanMessage
    msg_parts = request.params["message"]["parts"]
    text = " ".join([p.get("text", "") for p in msg_parts if p["type"] == "text"])
    result = await profile_agent.ainvoke({"messages": [HumanMessage(content=text)]})
    return JsonRpcResponse(
        id=request.id,
        result=TaskResult(
            id="task-profile",
            status=TaskStatus(state="completed"),
            artifacts=[TaskArtifact(content={"result": str(result)})],
        ),
    )


app.include_router(create_a2a_router(handler=handle_task))
