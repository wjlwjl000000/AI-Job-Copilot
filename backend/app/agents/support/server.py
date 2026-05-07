from fastapi import FastAPI
from app.a2a.server import create_a2a_router, mount_agent_card
from app.a2a.agent_card import create_agent_card
from app.a2a.types import JsonRpcResponse, TaskResult, TaskStatus, TaskArtifact

app = FastAPI(title="Support Agent")

agent_card = create_agent_card(
    agent_id="urn:agent:copilot:support",
    name="Support Agent",
    description="提供求职情感支持。当用户遭遇求职挫折、需要鼓励或共鸣时调用。从知识库中匹配相似的求职经历故事，生成温暖鼓励。仅被其他Agent通过A2A协议调用，不直接被Supervisor分派（Supervisor不应将用户的情感表达作为任务分派）。需要：用户当前的情绪表达或挫折描述。",
    url="http://localhost:8004",
    skills=[
        {"id": "comfort-user", "name": "情感鼓励", "description": "匹配相似求职经历，生成个性化鼓励内容", "examples": ["匹配度低时需要鼓励", "被拒后需要安慰"]},
    ],
)

mount_agent_card(app, agent_card.model_dump())


async def handle_task(request):
    from app.agents.support.agent import support_agent
    from langchain_core.messages import HumanMessage
    msg_parts = request.params["message"]["parts"]
    text = " ".join([p.get("text", "") for p in msg_parts if p["type"] == "text"])
    result = await support_agent.ainvoke({"messages": [HumanMessage(content=text)]})
    ai_msgs = [m for m in result.get("messages", []) if getattr(m, "type", "") == "ai"]
    answer = ai_msgs[-1].content if ai_msgs else str(result)
    return JsonRpcResponse(
        id=request.id,
        result=TaskResult(
            id="task-support",
            status=TaskStatus(state="completed"),
            artifacts=[TaskArtifact(content={"result": answer})],
        ),
    )


app.include_router(create_a2a_router(handler=handle_task))
