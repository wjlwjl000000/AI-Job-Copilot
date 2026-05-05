from fastapi import FastAPI
from app.a2a.server import create_a2a_router, mount_agent_card
from app.a2a.agent_card import create_agent_card
from app.a2a.types import JsonRpcResponse, TaskResult, TaskStatus, TaskArtifact

app = FastAPI(title="Matching Agent")

agent_card = create_agent_card(
    agent_id="urn:agent:copilot:matching",
    name="Matching Agent",
    description="负责职位匹配、匹配度评分和简历优化。当用户需要搜索匹配职位、评估与JD的匹配程度、或优化简历时调用。",
    url="http://localhost:8002",
    skills=[
        {"id": "match-jobs", "name": "职位匹配搜索", "description": "基于用户画像向量在Chroma中语义搜索匹配的职位", "examples": ["帮我搜搜适合我的职位"]},
        {"id": "score-match", "name": "匹配度评估", "description": "多维度评估简历与JD的匹配度", "examples": ["我和这个岗位匹配吗"]},
        {"id": "optimize-resume", "name": "简历优化", "description": "针对特定JD生成优化版简历", "examples": ["帮我优化简历"]},
    ],
)

mount_agent_card(app, agent_card.model_dump())


async def handle_task(request):
    from app.agents.matching.agent import matching_agent
    from langchain_core.messages import HumanMessage
    msg_parts = request.params["message"]["parts"]
    text = " ".join([p.get("text", "") for p in msg_parts if p["type"] == "text"])
    result = await matching_agent.ainvoke({"messages": [HumanMessage(content=text)]})
    return JsonRpcResponse(
        id=request.id,
        result=TaskResult(
            id="task-matching",
            status=TaskStatus(state="completed"),
            artifacts=[TaskArtifact(content={"result": str(result)})],
        ),
    )


app.include_router(create_a2a_router(handler=handle_task))
