from fastapi import FastAPI
from app.a2a.server import create_a2a_router, mount_agent_card
from app.a2a.agent_card import create_agent_card
from app.a2a.types import JsonRpcResponse, TaskResult, TaskStatus, TaskArtifact

app = FastAPI(title="Interview Agent")

agent_card = create_agent_card(
    agent_id="urn:agent:copilot:interview",
    name="Interview Agent",
    description="当用户获得面试机会、需要生成针对性面试问题或评估模拟回答时调用。需要具体JD内容和用户弱项领域。不要用于简历解析或职位搜索场景。",
    url="http://localhost:8003",
    skills=[
        {"id": "generate-interview-qs", "name": "生成面试问题", "description": "基于JD+弱项生成针对性面试题", "examples": ["帮我准备面试"]},
        {"id": "evaluate-answer", "name": "评估回答", "description": "评估面试回答质量并给出改进建议", "examples": ["评估我的回答"]},
    ],
)

mount_agent_card(app, agent_card.model_dump())


async def handle_task(request):
    from app.agents.interview.agent import interview_agent
    from langchain_core.messages import HumanMessage
    msg_parts = request.params["message"]["parts"]
    text = " ".join([p.get("text", "") for p in msg_parts if p["type"] == "text"])
    data = {}
    for p in msg_parts:
        if p["type"] == "application/json":
            data.update(p.get("content", {}))
    prompt = f"{text}\n任务数据: {data}" if data else text
    result = await interview_agent.ainvoke({"messages": [HumanMessage(content=prompt)]})
    ai_msgs = [m for m in result.get("messages", []) if getattr(m, "type", "") == "ai"]
    answer = ai_msgs[-1].content if ai_msgs else str(result)
    return JsonRpcResponse(
        id=request.id,
        result=TaskResult(
            id="task-interview",
            status=TaskStatus(state="completed"),
            artifacts=[TaskArtifact(content={"result": answer})],
        ),
    )


app.include_router(create_a2a_router(handler=handle_task))
